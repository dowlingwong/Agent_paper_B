# E-SYN worlds and certified oracle gains (build runbook P3; BUILD_LIST B3 + B17; revised after review rounds 1 and 2)

**AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.** Synthetic worlds are implementation checks
and oracle gaps; they are never evidence about the real loop (plan §5).

- **Data:** `paperC/esyn/oracle_table_v1.json` (schema `paperc_esyn_oracle_table/v2`), produced by
  `python -m paperc.esyn.table` in about 25 minutes on two processes. The table stores a fingerprint of the E-SYN
  sources, and a test fails if the table is stale.
- **Tests:** `paperC/tests/test_esyn_p3.py`, plus the schema tests. The full paperC suite has 147 tests, all passing.
- **Revision.** Round 1 of the independent review (`reviews/BUILD_P3_REVIEW_20261116.md`) found four MAJOR issues.
  The fixes are listed in `reviews/BUILD_P3_RESPONSE_R1_20261116.md`. Several round-1 numbers changed:
  - keep_feedback fell from +0.0024 to +0.0015, after the static grid was extended;
  - information rose from +0.0010 (uncertified) to +0.0064 (certified), with Track S's schedule as the member;
  - every tolerance is now 5 % of a declared reference gain.
- **Round 2: ACCEPT**, with 5 MINOR findings, fixed in `reviews/BUILD_P3_RESPONSE_R2_20261116.md`:
  - corrected explanations of the information member and the null;
  - a caveat on the coarse static grid;
  - the fingerprint now covers the table producer.

  The table was rebuilt in full; every number is unchanged.

## 1. What was built

| Module | Content |
|---|---|
| `esyn/worlds.py` | Track S world mechanism, ported unchanged from `trackS-ops-20261030` @ `fab88fc`. Tested against the pinned original (components), and at loop level: Paper C's campaign values equal Track S's simulator for N0, P1, P2+ and P0 |
| `esyn/extra.py` | `ESynWorld`: a Track S world plus Paper C's declared data (channel, declared gain sign, reference gain, discrete size law, interaction matrix, comparison model, offered epochs); the registry of 7 worlds |
| `esyn/sim.py` | the campaign simulator: Paper B's loop as Track S runs it, plus `verify`, `reaudit` (offered only right after a keep) and `final`. It writes `spt_transition/v1` rows that `check_campaign` accepts with propensity replay and the seed registry; any record is regenerated from its `instance_seed` |
| `esyn/policies.py` | static rules (Paper B's class), the DP threshold policy, `Dynamic` (budget, information and novelty terms), `InteractionAware` (privileged), `EvalAlloc`, and Track S's 9-threshold `Schedule` |
| `esyn/families.py`, `esyn/oracle.py` | the certified oracle (below) |
| `esyn/dp.py` | exact backward induction for the budget world, and the exact value of every static threshold |
| `esyn/table.py` | the table, the B17 decomposition, the W calibration and the code fingerprint |
| `schema.py` | amendment of 16 Nov: optional `State.candidates` on `final` rows; rows without candidates stay readable by the 15 Nov validator; consistency checks |

**Certified oracle:**
- **Static search.** The best static rule is found on a static grid that is extended until it is interior (g = 0 is
  the only natural bound).
- **Member search.** The world's member families are searched by coordinate ascent: the channel parameter, then
  the (g, h) neighbourhood; every grid is extended at non-natural edges.
- **Evaluated member.** The best member that decides differently from the static rule. It is evaluated against the
  static rule on a disjoint block, paired, and sized until the 95 % half-width is at most 5 % of a **declared**
  reference gain:
  - 0.5 σ_cmp = 0.0033, Track S's 0.5 σ;
  - the exact DP gain in the budget world.

  The tolerance is therefore an absolute precision of 0.000165, as in Track S.
- **Deviation from Track S.** Only the selected member is certified, not every member.
- **Lower bounds.** Gains are family-best lower bounds, except in the budget world.
- **Coarse static grid.** The static grid is extended at its edges but never refined near the optimum, so the
  baseline can sit slightly below the best static rule. In information, a finer grid beats the selected static by
  0.00022 ± 0.00008 (review round 2), a few percent of that gain and more than the tolerance. A refinement pass is
  an open item before P4 uses these gains as oracle references.

## 2. Worlds

| World | Channel on | W | Comparison | Epochs | Mechanism |
|---|---|---|---|---|---|
| strict_null | none | 40 (not binding) | increment | E1, E2 | fresh keys, discrete sizes; the myopic Bayes rule is optimal |
| budget | budget | 8 | increment | E1, E2 | as strict_null, but about 18 executable proposals compete for 8 runs |
| interaction | incumbent interaction | 40 | increment | E1, E2 | 4 recurring keys; pairs (0,1), (2,3) complement by 0.012: the first kept key of a pair adds M to its partner's later increment |
| shared_error | shared incumbent error | 60 (not binding) | config | E1, E2, reaudit | a kept candidate's recorded value carries its selected measurement error into later comparisons until re-audit |
| eval_allocation | evaluation control | 40 | config | E1, E2, verify, reaudit, final | verify, re-audit and final selection under the shared-error model; extra measurements cost runs |
| information | information (Track S P1-diffuse) | 10 | increment | E1, E2 | probes open keys whose size-16 follow-ups are large and noisy (strength 16; Track S ANALYSIS_NOTES §5.1 grid) |
| keep_feedback | keep feedback (Track S P2+-diffuse) | 10 | increment | E1, E2 | an early keep raises the θ mean of the next proposals (strength 0.012; same grid) |

**Measurement model.** In config worlds one run measures a configuration with sd σ_cmp/√2. The loop compares the
candidate's mean measurement with the incumbent's recorded mean.

**Belief model.** A2-U's keyed conjugate model.

**Privileged knowledge.** The interaction world's oracle member knows the true matrix M. It reads a
`privileged:interaction` forecast, which is written only for policies that declare `privileged = True`. Its gain
is therefore the value of an M-aware keep rule, an upper reference rather than a learnable target. Learners and
baselines must exclude `privileged:*` forecasts, and a test checks that no other policy's rows carry one.

**shared_error.** Re-audits there are free (W never binds), so this world certifies that free re-audits pay against
the shared incumbent error. No member exploits the error through E1/E2 decisions alone.

**Campaign value.** Y = true value of the final configuration minus y0, with no audit noise.

## 3. Oracle table (5 % of the declared reference; selection 2,000, pilot 1,000, n_max 400,000)

| World | W | Best static (grid) | Best member (family) | Reference gain | Gain ± 95 % hw | hw / gain | n | Certified |
|---|---|---|---|---|---|---|---|---|
| strict_null | 40 | `static:0,0` | `schedule:0,0,0,0,0.0005,0;0,0,0;0.02` (schedule) | 0.00330 (0.5 sigma_cmp) | +0.00000 ± 0.00000 | — | 1000 | exact (DP) + per-family evaluation |
| budget | 8 | `static:0.001,0` | `dp` (dp) | 0.00211 (DP gain) | +0.00205 ± 0.00010 | 4.9% | 11646 | yes |
| interaction | 40 | `static:0,0` | `interaction:0,0,0.25` (interaction_beta) | 0.00330 (0.5 sigma_cmp) | +0.00124 ± 0.00016 | 12.6% | 3485 | yes |
| shared_error | 60 | `static:0,-0.001` | `evalloc:0,0,0,1,3,incumbent` (reaudit_k) | 0.00330 (0.5 sigma_cmp) | +0.00212 ± 0.00016 | 7.6% | 6562 | yes |
| eval_allocation | 40 | `static:0,-0.001` | `evalloc:0,-0.001,0.25,3,2,incumbent` (evalloc) | 0.00330 (0.5 sigma_cmp) | +0.00365 ± 0.00016 | 4.5% | 7469 | yes |
| information | 10 | `static:0.0015,0.001` | `schedule:0,0.0015,0.003,0.0005,0.002,0.005;0,0.001,0;0.02` (schedule) | 0.00330 (0.5 sigma_cmp) | +0.00643 ± 0.00015 | 2.4% | 238026 | yes |
| keep_feedback | 10 | `static:0.0005,-0.005` | `dynamic:0.0005,0,0,0,0.016,0,inf` (keep_budget) | 0.00330 (0.5 sigma_cmp) | +0.00154 ± 0.00016 | 10.5% | 4644 | yes |

**Reading the table:**
- The gain is the evaluated member's paired difference from the best static rule on the evaluation block.
- "hw / gain" is the relative precision against the measured gain.
- "Certified" means hw ≤ 0.05 × reference and n_max was not reached.

**Budget world.**
- The member is the exact DP policy. DP value 0.01139 against the selected static's exact value 0.00928 (g = 0.001):
  exact gain 0.00211. The oracle measures 0.00205 ± 0.00010.
- On the evaluation block, both means lie within 4 se of their exact values (DP 0.01143, static 0.00938).

**Strict null.**
- The DP equals the static rule g = 0 exactly: gain 0 to machine precision, because W does not bind.
- The selected member, a schedule differing in one rarely used threshold, never decides differently on the
  evaluation pilot, hence 0 ± 0. So each family's best member was also evaluated on 5,000 evaluation campaigns:

  | Family | Best member | Gain ± 95 % hw | Share of campaigns deciding differently |
  |---|---|---|---|
  | Dynamic | `dynamic:0,0.001,0,0.004,0.002,0,0.02` | −0.00046 ± 0.00012 | 86 % |
  | Schedule | `schedule:0,0,0,0,0.0005,0;…` | 0.00000 ± 0.00000 | 0 % |

  No member beats the static rule. The schedule family adds no falsification power here, because the exact DP
  already dominates every schedule. The null result rests on the exact DP and on the Dynamic family's evaluation.

**Families compared in keep_feedback.** On the selection block, the budget-dependent keep threshold
(b_keep = 0.016, after the grid was extended) reached +0.00155 and Track S's schedule +0.00140. The former was
evaluated.

**Track S comparison.** Track S's schedule gains (ANALYSIS_NOTES §5.1, its own δ_Y units) were about 3.8 δ_Y ≈ 0.0126
in P1-diffuse-16 and about 1.9 δ_Y ≈ 0.0064 in P2+-diffuse-0.012. The E-SYN gains (0.0064 and 0.0015) are lower
bounds from these families. The keep-feedback gap to Track S's schedule is not explained here.

## 4. Evaluation control (B17): per-action values

**Decomposition** on a third, disjoint block (3,000,000 + i, n = 20,000). It uses eval_allocation at W = 40 and the
evaluated member's thresholds (g = 0, h = −0.001, verify band 0.25, verify up to 3 measurements, re-audit up to 2):

| Policy | Gain over the best static (± 95 % hw) | Share of campaigns deciding differently |
|---|---|---|
| verify only | +0.00194 ± 0.00009 | 91 % |
| re-audit only | +0.00149 ± 0.00009 | 88 % |
| verify + re-audit, final = incumbent | +0.00361 ± 0.00010 | 96 % |
| verify + re-audit, final = best recorded | +0.00348 ± 0.00010 | 96 % |

**Final selection alone** (best recorded minus incumbent, same measurement policy):
- **W = 40:** −0.00013 ± 0.00003 (30 % of campaigns differ);
- **W = 60, with re-audit up to 3:** **+0.00021 ± 0.00003** (31 % differ).

So final selection has a demonstrated value, and its sign depends on the budget. With few repeated measurements, the
recorded values of earlier incumbents are too noisy, and selecting among them loses the later keeps' gains.

**W calibration** (selection block, n = 1,000, current code; best member of the family minus best static, ± se):

| World | W = 24 | W = 32 | W = 40 | W = 60 |
|---|---|---|---|---|
| shared_error | −0.00066 ± 0.00027 | — | — | +0.00221 ± 0.00022 |
| eval_allocation | −0.00022 ± 0.00024 | +0.00228 ± 0.00023 | +0.00366 ± 0.00021 | +0.00583 ± 0.00023 |

These runs motivated the budgets: shared_error at 60, eval_allocation at 40. At W = 24 no evaluation-control member
beats the static rule.

## 5. Findings (E-SYN only)

1. **Every declared channel shows a certified positive oracle gain** over an interior best static rule. The
   strict null shows none. These are lower bounds from small families, except the budget world's exact DP gain.
2. **Information has the largest gain** (+0.0064). It comes from a 9-threshold schedule after Track S's (budget
   position = runs used / W; a fixed τ split at 0.02). The gain comes almost entirely from the dependence on the
   budget third: about +0.0060 without the τ split, against +0.0001 for a τ split alone (review round 2). The
   selected schedule's E1 thresholds by budget third:

   | Budget third | Small-τ proposals (probes, fillers) | Large follow-ups |
   |---|---|---|
   | first | 0 (execute all) | 0.0015 |
   | middle | 0.003 (strict) | 0.0005 (lenient) |
   | last | 0.002 | 0.005 (strict) |

   Round 1's key-novelty member still gains about +0.0010 over the same best static (review round 2, 100,000 fresh
   campaigns). The schedule replaced it because its gain is about six times larger. Round 1's explanation, that the
   novelty gain vanished once the static grid was interior, was wrong: this world's best static did not change.
3. **Evaluation control pays only with enough runs.** Verify and re-audit each add value at W = 40, and their sum
   is close to additive. Final selection helps only when re-audits make recorded values reliable (W = 60). At
   W = 24 nothing beats the static rule.
4. **Keep-feedback.** About half of round 1's apparent gain was a level shift of the keep threshold, which a static
   rule recovers (best static h = −0.005). The remaining +0.0015 needs a budget-dependent threshold.
5. **The best static rule partly compensates the winner's curse** in the config worlds (h = −0.001, below the Bayes
   threshold 0). The evaluation-control members still beat it.

## 6. Deviations and choices to review

- **Schema amendment (dated 16 Nov 2026).** Optional `State.candidates` on `final` rows, with:
  - row rules (only on final rows; the selection is among them);
  - campaign checks (unique hashes; every candidate was an incumbent earlier, with the record it last had).

  `to_dict` omits an empty list, so all other rows remain readable by the P1 validator of 15 Nov.
- **One certified member per world** (Track S certified every member). Gains are family-best lower bounds.
- **Coordinate-ascent member search** on the selection block, with grids extended at non-natural edges. The
  selected static and member are interior in every world, and a test checks this.
- **Calibration history.** The first calibration had two faults:
  - wrong Track S strengths (P1 0.02, P2+ 0.004);
  - member grids without the static's thresholds.

  The strengths were corrected from Track S's notes, and two budgets were set from the calibration above
  (shared_error 24 → 60, eval_allocation 24 → 40). Round 1 also had a truncated static grid, which inflated
  keep_feedback and information. The null and the channel mechanisms were never changed.
- **Re-audit timing.** Re-audit is offered only right after a keep, so its timing is not a decision.
- **RNG.**
  - Every campaign draws from `SeedSequence([60001, world code, i])`; key 60001 is claimed in the seed registry.
  - Recorded campaigns use i = 0 … 9,999 (`instance_seed` 50000 + i); their audit seeds are nominal labels.
  - Oracle blocks use i = 1,000,000 + j (selection), 2,000,000 + j (evaluation) and 3,000,000 + j (decomposition).
    These are numerically inside Paper B's `tracks_oracle_*` ranges, but they enter only the Paper C root key.
- **Not yet in E-SYN.** Track S P0 and P2− (Track S found no gain ≥ 1 δ_Y there). Pairs of channels. Fork designs
  (P6).

## 7. Next

- P4: the policy interface and the non-RL ladder on these worlds, with B18's sequential-testing comparators. The
  certified gains above are P4's oracle references.
- The interaction world's privileged member should be read as an upper reference.
