# Review of Track S runbook, revision 5 (29 Oct 2026)

AI-assisted review (fresh agent); read-only; authorizes nothing.

**Scope.** `RB` = rev-5 runbook; `R4` = rev-4 review. Spot-checks against the snapshots all held: h `campaign.py`:1287 (the loop exits when `compute_budget.exhausted`, so a binding W ends the campaign), h `budget.py`:59–75, h `langgraph_manager.py`:55–71 (seed keyed on `campaign_id`, trial, repetition) and :122–141 (the prompt shows the trial index, not runs left), apb `control.py`:16–23, `features.py`:257/385, `arms.py`:122–131, NOISE_FLOOR_COMMON Table 1, LIVENESS:78–79, PLAN:518.

**Verdict: REVISE (narrow).** 1 BLOCKING, 4 MAJOR, 8 MINOR. The structure is now right: a tuned dynamic family against a tuned static rule, Holm/IUT sizing, a fixed-effect calibration and exact placebos. What remains blocking is one sign error together with the calibration gap that hides it.

## 1. Revision 4 → 5 (body checked)

| Finding | Verdict | Reason |
|---|---|---|
| BL-1 | PARTIAL | The tuned-family design, the excluded zero member, the flip-rate gate, the fixed-δ_Y planting and the wording are all in (RB:98–99, 126, 134). But the family's budget term has the wrong sign, and S0.7 has no budget control (BL-1 below). Selection noise makes the power gate likely to fail (MA-1). |
| BL-2 | ACCEPT | ≥ 18/200 is p ≈ 0.008 under 5 %. 2.90 gives 0.83 (Holm, one node) and 0.895² = 0.80 (IUT). The exact and descriptive placebos are as recommended (RB:99, 139, 143–144). |
| MA-1 | ACCEPT | The order is explicit, m̃ is gone and the blocks are disjoint. The rows do not say that dev instances are shared across configurations (MA-1). |
| MA-2 | ACCEPT | A-small with precedence. The LB definition is ambiguous (mi-2). |
| MA-3 | ACCEPT | ≥ 20 pairs, 80 % χ² UCL, n_max and the σ_D = 0.02 rows are in. What B means on a node set with one A-only node is new (MA-4). |
| MA-4 | ACCEPT | Static is nested by construction and tested. π′ has a nesting test. |
| MA-5 | PARTIAL | The b_info = 0 secondary exists, but it tests a wrong-signed budget term. "Survives" (RB:30) is undefined on ≥ 30 instances. |
| mi-1, mi-3–mi-9 | ACCEPT | All in the body. Instance keys need code because `manager_seed` takes `campaign_id`; they are listed in S0.3. |
| mi-2 | PARTIAL | S0.5 is 20×2 + 10×2 = 60 campaigns, not 50. The wall time omits worker and audit time (mi-5). |

## 2. BLOCKING

**BL-1. The budget term points the wrong way, and nothing in the plan would notice.**

r = runs_left/W − proposals_left/N_cap is positive when runs are abundant. A knapsack threshold must then *fall*. The rule g0 + b_budget·r with b_budget ∈ {0, **+1**} σ_node raises it. RB's own D1′ example shows this: after a skip, r = 1 − 1/2 = 0.5, and the optimum executes anything, while b = +1 raises the bar. Three things follow.
- The budget channel, the one violation with a proven gain (D1′, element 2), cannot be expressed. Four of the seven eligible members carry the harmful term.
- S0.7 plants only P1 (information) and P2 (keep). No control would detect the error, so the "budget alone" secondary and the "dynamic-knapsack" wording for A both become meaningless.
- After the sign is fixed, **N0 (NF + NI) is not a null at a binding W.** A state-dependent threshold beats every static one even with i.i.d. values (the D1′ example is i.i.d.). The N0 route-A rate can then exceed 18/200 legitimately, and a STOP would fire.

*Fix:*
- b_budget ∈ {−1, 0} σ_node, or two-sided, with a unit test on the D1′ example.
- Add a synthetic budget-channel control P0 (planted gain = δ_Y), included in the power gate.
- Define each null by its oracle gain: the large-replication value of the best eligible member minus the best static rule is ≤ 0, for example at non-binding W or with a constant V*. Do not define the null by "NF + NI".
- Make h_budget two-sided, and plant P2 in both signs. The sign of the best keep offset is not known a priori.

## 3. MAJOR

**MA-1. With 10 dev instances per configuration, selection is close to noise at δ_Y, so real power is about half the nominal and the S0.7 gate will likely remove B.**

Assume σ_D ≈ 0.01 and common dev instances. The sd of a member-vs-member mean difference is then 0.01/√10 ≈ 0.0032: about 1.0 δ_Y on digits and 1.6 δ_Y on tabular. Suppose one of seven members carries δ_Y. P(select it) is about 0.55 on digits and 0.35 on tabular (normal approximation, not a run). End-to-end power is then about 0.8 × P(select), roughly 0.45 and 0.30, which is below the "power LB ≥ 0.6" gate. Unequal-instance tuning would be worse. S0.7 sits after S0.6, so a failed gate leaves no remedy: the track can then end only in A or inconclusive.

*Fix:*
- Run every configuration on the **same** dev instance keys.
- Shrink the eligible set to one member per channel (≈ 3), or use paired racing (irace-style) with a declared total.
- Run S0.7 **before** S0.6, with one pre-declared resizing of dev instances if the gate fails.
- Have S0.7 match the campaign-level paired σ_D and the dev between-configuration sd, not only the per-fork noise.
- Report P(correct selection).

**MA-2. A can reflect a static shift, not dynamics.**

π\* inherits (g0, h0) from a noisily selected m\*. The static keep grid is one-sided (h ∈ {0, −0.25 σ}). At W ≈ 10 with about 6 (key, sign) groups, "new" (fewer than 2 executions) is true for most decisions, so b_info acts mostly as a τ-scaled constant offset. A member can therefore beat m\* by re-thresholding. *Fix:*
- Make the h grid two-sided.
- On the ≥ 30-instance secondary subset, also run the static rule at π\*'s mean realised thresholds, and m\*'s grid neighbours.
- Word A as "dynamic" only if π\* also beats that static projection. Otherwise word it "the tuned static rule was mis-set".

**MA-3. σ_node is a fixed-split quantity, but Track S runs `vary`.**

The grids (g, e2off, b_budget, h_budget) and δ_Y use the fixed-split values 0.0066 and 0.0019 (RB:80, 138). Tabular's split sd under `vary` is 0.0123. On tabular, g ∈ {0.0001 … 0.0008} and b_budget·r ≈ 0.0005 are tiny against a `vary`-scale V̂\*. That risks a degenerate static grid and a flip rate below 10 %, which would make B unavailable for an artefactual reason. *Fix:* scale the grids by an S0.5 `vary` paired σ, and state that δ_Y is a declared raw-unit constant.

**MA-4. B on a node set with an A-only node is undefined.**

At σ_D = 0.01 the χ² UCL (19 df) is ≈ 0.0118, which gives n_tabular ≈ 293, at the edge of n_max. RB:134 requires n ≤ n_max on "those nodes" for B, but S0.5b says only that the node "can support A but not B". *Fix:* pre-declare one of two rules. Either B is decided on the remaining node(s), worded per node, with the run size min(n, n_max), or B is globally unavailable.

## 4. MINOR

- **mi-1.** Define the flip rate: both rules are evaluated on the same visited states (pooled dev trajectories), excluding rule skips and post-exhaustion trials, with E1 and E2 reported separately.
- **mi-2.** A-small: use Holm-adjusted rejections throughout, and state the precedence of A-small vs B (both are headline-B).
- **mi-3.** σ_D comes from A2-U at g = 0.1 vs 0.3 at W = cap. Recompute it at the chosen W from truncated ledgers. Truncation is exact for A2-U: the prompt has no runs-left field and the loop stops at W. Audit the truncated incumbents. Before S0.8, take the maximum with the S0.6 paired π\* vs m\* UCL.
- **mi-4.** Run the exact placebo first, in the first S3e instances or at S0.5, so that a rare non-determinism cannot void the track after outcomes exist. S0.1's 200 calls are fewer than one placebo block (400).
- **mi-5.** Cost: the ≈ 40 calls per campaign are an upper bound, since a binding W ends the campaign early, which is good. The wall time omits worker and audit runs: digits ≈ 2.5 s × (W + 5) ≈ 40 s per campaign against ≈ 60 s of LLM time at 1.5 s per call. Add tabular's run time. S0.3's scope makes 2–4 days optimistic.
- **mi-6.** The all-zero dynamic member uses 10 dev campaigns. Declare it as a paired re-measurement of m\* (it feeds the winner's-curse report), and say that π\* effectively had 7 configurations plus m\*'s tuning.
- **mi-7.** Report the binding share under m\* and π\* in S3e. W is fixed under A2-U at g = 0.1, and m\* may sit at g = 0.4.
- **mi-8.** DAC lens: describe π\* as a "tuned parametric dynamic threshold (≤ 3 coefficients, 2-level grid)", not a learned DAC policy, and cite AC racing. The instances are seeds (this is already in the limitations).

## 5. Notes

- **Route B honesty.** The wording (RB:32) is honest and correctly scoped to the family and the tuning budget. Its UB statement about the selected π\* is valid whatever the S0.7 power. Reachability, however, currently hinges on MA-1, MA-3 and MA-4.
- **Pairing and verify-off** are sound.
- **Seed blocks and step order** are sound, except that S0.7 should precede S0.6.

## 6. What blocks acceptance

Only **BL-1**: correct the sign of b_budget (with a test), add a budget-channel synthetic control to the power gate, and define N0 by zero oracle gain. Fix MA-1 and MA-3 in the same revision; otherwise B is probably unreachable on tabular. Once BL-1 is fixed and MA-1, MA-3 and MA-4 are addressed, I expect ACCEPT WITH MINOR CHANGES.
