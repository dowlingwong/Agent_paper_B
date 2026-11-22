# E-SYN: learner data-scaling curve and headroom table

**AI-assisted (Claude, chat session, 22 Nov 2026). ENGINEERING_ONLY. Not evidence, not an author decision.** Run by `python -m paperc.esyn_scaling`; rendered by `python -m paperc.esyn_scaling_report`; data in `paperC/esyn/scaling_v1.json`.

## 1. Question

P8 (`LEARNER_VALIDATION_20261117.md`) trained N6, R0 and R1 on 4,096 logged roots of the short budget world. Both offline-RL learners ended below the best static rule. This report asks whether that is a matter of training size, and how much room each E-SYN world leaves above simple rules.

## 2. Design (fixed before the run)

- **World and data:** P8's short budget world (8 slots, 4 runs), P8's N1 baseline, logging mixture, support roots, dev roots and test roots.
- **Sizes:** 256, 512, 1,024, 2,048, 4,096, 8,192 training roots. Draw 0 is nested: it starts with P8's roots and adds unused ones above 4,096. Further draws use separate root slices where one fits: three draws up to 2,048 roots, two at 4,096, one at 8,192.
- **Largest size:** the seed registry limits recorded campaigns to instances 0 … 9,999, and the support roots take 768 of them. 8,192 roots is therefore the largest power of two this world can log. A longer curve needs a new registry block.
- **Settings:** P8's three settings per method. R0 gets one larger setting (63 leaves, 128 rounds). R1 gets one wider, longer-trained setting (width 64, 12,800 critic steps, 4,800 actor steps). N6 keeps P8's grid.
- **Selection:** highest mean paired dev gain over N1, ties in grid order. Selection is done within P8's grid and, separately, within the extended grid. The selected setting is refitted for three fit seeds and tested once.
- **Support gate:** recorded for every training set and every selected policy, but not enforced. A row marked *below gate* is not a deployable policy under P8's rules.
- **Test statistic:** mean paired gain over N1 on the 6,000 test roots, averaged over three fit seeds. The interval covers test-root variation given the fitted policies. It does not cover the training draw; the draw-to-draw range in §4 shows that part.

## 3. Reference values (exact)

N1 0.00119991; best static rule 0.00218046; DP 0.00226813. The N1-to-DP gap is 0.00106822. The best static rule takes 91.8% of that gap, so a learner has 8.2% of the gap left to win over it.

On the test roots, paired simulation gives DP − N1 = 0.00101557 (s.e. 0.00004888) and static − N1 = 0.00093040 (s.e. 0.00004850). The shares below divide by the exact gap, as P8 does. On these test roots the best static rule therefore reads 87.1% of the exact gap; compare the learners with that number, or use the paired column.

## 4. Scaling curve

Share of the exact N1-to-DP gap recovered on the test roots, extended grid, draw 0 (95% interval over test roots). “vs static” is the paired difference to the best static rule in units of 10⁻⁵, with its 95% interval.

| Training roots | Logged decisions | Support gate | N6 share | N6 vs static | R0 share | R0 vs static | R1 share | R1 vs static |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 256 | 2,632 | below gate | 81.7% [72, 91] | -5.8 [-11.0, -0.6] | 0.2% [-10, 10] | -92.9 [-102.3, -83.4] | 72.7% [64, 81] | -15.4 [-18.7, -12.0] |
| 512 | 5,249 | below gate | 88.9% [80, 98] | +1.9 [-2.5, +6.2] | 18.0% [7, 29] | -73.8 [-83.1, -64.4] | 82.9% [74, 92] | -4.5 [-6.8, -2.2] |
| 1,024 | 10,507 | below gate | 85.5% [76, 95] | -1.7 [-5.5, +2.1] | 43.8% [34, 53] | -46.2 [-54.7, -37.8] | 83.3% [74, 92] | -4.1 [-6.7, -1.4] |
| 2,048 | 20,952 | passes | 86.6% [77, 96] | -0.5 [-4.6, +3.6] | 62.6% [53, 72] | -26.2 [-33.6, -18.9] | 77.6% [68, 87] | -10.1 [-15.6, -4.6] |
| 4,096 | 41,961 | passes | 88.6% [79, 98] | +1.6 [-2.4, +5.5] | 68.5% [59, 78] | -19.9 [-26.5, -13.3] | 84.1% [75, 93] | -3.2 [-5.7, -0.7] |
| 8,192 | 83,712 | passes | 87.5% [78, 97] | +0.4 [-3.3, +4.2] | 70.2% [60, 80] | -18.1 [-24.5, -11.7] | 82.3% [73, 91] | -5.1 [-8.0, -2.2] |

Selected settings (extended grid, draw 0) and the candidate-policy support check:

| Training roots | R0 setting | R0 policy support | R1 setting | R1 policy support | N6 setting |
|---:|---|---|---|---|---|
| 256 | 63 leaves, 128 rounds | below gate | τ=0.8, β=8, width 32, 3,200 steps | below gate | α=5 |
| 512 | 31 leaves, 64 rounds | below gate | τ=0.9, β=16, width 32, 3,200 steps | below gate | α=50 |
| 1,024 | 7 leaves, 36 rounds | below gate | τ=0.9, β=16, width 32, 3,200 steps | below gate | α=5 |
| 2,048 | 7 leaves, 36 rounds | passes | τ=0.9, β=16, width 64, 12,800 steps | passes | α=0.25 |
| 4,096 | 7 leaves, 36 rounds | passes | τ=0.9, β=16, width 32, 3,200 steps | passes | α=5 |
| 8,192 | 7 leaves, 36 rounds | passes | τ=0.8, β=8, width 32, 3,200 steps | passes | α=0.25 |

Draw-to-draw range of the share (extended grid; minimum – maximum over the available draws):

| Training roots | Draws | Gate passes in | N6 | R0 | R1 |
|---:|---:|---:|---:|---:|---:|
| 256 | 3 | 0 | 77.9% – 86.2% | -96.8% – 0.2% | 72.7% – 79.2% |
| 512 | 3 | 0 | 84.3% – 88.9% | -5.4% – 18.0% | 78.4% – 82.9% |
| 1,024 | 3 | 0 | 85.5% – 89.4% | 27.5% – 54.8% | 80.6% – 83.9% |
| 2,048 | 3 | 3 | 86.6% – 87.6% | 55.2% – 62.6% | 77.6% – 88.6% |
| 4,096 | 2 | 2 | 87.6% – 88.6% | 68.5% – 80.5% | 84.1% – 88.7% |

P8 grid only (draw 0), for comparison with P8:

| Training roots | R0 share | R0 setting | R1 share | R1 setting |
|---:|---:|---|---:|---|
| 256 | -32.2% | leaves=31, rounds=64 | 72.7% | expectile=0.8, inverse_temperature=8 |
| 512 | 18.0% | leaves=31, rounds=64 | 82.9% | expectile=0.9, inverse_temperature=16 |
| 1,024 | 43.8% | leaves=7, rounds=36 | 83.3% | expectile=0.9, inverse_temperature=16 |
| 2,048 | 62.6% | leaves=7, rounds=36 | 80.0% | expectile=0.8, inverse_temperature=8 |
| 4,096 | 68.5% | leaves=7, rounds=36 | 84.1% | expectile=0.9, inverse_temperature=16 |
| 8,192 | 70.2% | leaves=7, rounds=36 | 82.3% | expectile=0.8, inverse_temperature=8 |

## 5. Reproduction of P8

At 4,096 roots (draw 0, P8 grid) the training batch has the same number of logged decisions as P8: **yes**; the same number of fork points: **yes**.

| Method | Same setting selected | Same fitted policies | P8 gain | This run | Difference |
|---|---|---|---:|---:|---:|
| N6 | yes | no | +0.00094604 | +0.00094604 | +0.00e+00 |
| R0 | yes | yes | +0.00073121 | +0.00073121 | +0.00e+00 |
| R1 | yes | no | +0.00089924 | +0.00089851 | -7.27e-07 |

Library versions of this run: torch 2.15.0+cu132, LightGBM 4.7.0, NumPy 2.5.3. P8 did not store its versions, so a difference in a fitted policy can come from the library version.

Code hash stored in the data file: `7f4ce03985d5b8e0…`; it matches the committed `esyn_scaling.py` and its sources.

## 6. Headroom table (stored P3 and P4 tables, no new simulation)

Each world's P4 ladder was tested on 10,000 common roots. The gap is oracle member − N1, where N1 is the static rule tuned on dev roots. Two groups of hand-built rows are compared with it:

- **one-step rules** (N2, N2b, margin, shrink, rawkeep): each proposal is decided on its own forecast;
- **hand-built sequential rules** (N3, N4, kg, race, sprt): they read the campaign state, such as the budget left or earlier measurements of the same configuration.

“Left” is what remains between the best hand-built row and the oracle member, with its 95% half-width. It is the room a learned policy could win over rules written by hand. σ is the world's comparison noise.

| World | Gap, 10⁻³ | Gap / σ | Best one-step rule: share of gap | Best sequential rule: share of gap | Left, 10⁻³ | Left / σ | Room for a learner |
|---|---:|---:|---:|---:|---:|---:|---|
| budget | 2.229 ± 0.117 | 0.34 | N2b: 4.1% | N4: 100.7% | -0.016 ± 0.028 | -0.00 | none shown: a hand-built rule reaches the oracle member |
| eval_allocation | 3.661 ± 0.141 | 0.55 | rawkeep: 14.1% | sprt: 67.4% | 1.195 ± 0.135 | 0.18 | yes |
| information | 5.893 ± 0.747 | 0.89 | N2: 3.2% | N3: 78.5% | 1.265 ± 0.690 | 0.19 | not resolved |
| interaction | 1.102 ± 0.096 | 0.17 | shrink: 39.7% | N3: 3.7% | 0.665 ± 0.108 | 0.10 | yes |
| keep_feedback | 1.315 ± 0.152 | 0.20 | margin: 84.8% | N3: 124.2% | -0.319 ± 0.218 | -0.05 | none shown: a hand-built rule reaches the oracle member |
| shared_error | 2.210 ± 0.133 | 0.33 | rawkeep: 26.4% | N3: 4.4% | 1.627 ± 0.123 | 0.25 | yes |
| strict_null | -0.003 ± 0.020 | -0.00 | shrink: — | N4: — | -0.012 ± 0.027 | -0.00 | none: no gap |
| p8_short_budget (exact; §4's world) | 1.068 | 0.16 | static threshold: 91.8% | not run | 0.088 | 0.01 | 8.2% of the gap, above a one-step rule |

Reading rules for this table:

- The oracle member is the best member of a declared family, except in the two budget worlds and strict_null, where an exact DP exists. Elsewhere “left” is a lower bound on the true room, and a hand-built rule tuned on dev roots can exceed the oracle member.
- A share is shown only where the gap exceeds twice its half-width.
- “yes”: “left” exceeds twice its half-width. “none shown”: “left” does not exceed its half-width. “not resolved”: in between. The intervals are not corrected for the number of rows read.
- The table says how much room exists. It does not say that R0, R1 or N6 can take it: those learners act on E1 and E2 only, and the worlds with room need actions they do not have (re-measure, re-audit) or state they do not see (which keys interact).

## 7. Reading (written by the recorder for `scaling_v1.json`; AI-assisted)

On the test roots the best static rule reads 87.1% of the exact gap and the DP 95.1%. A learner that matters has to land between those two numbers.

**1. P8's result is not an effect of the training size, within the sizes this world can log.**
- **R0 (fitted Q iteration)** depends strongly on the data: 0.2% of the gap at 256 roots, 43.8% at 1,024, 68.5% at 4,096 and 70.2% at 8,192. The curve flattens: the last doubling adds 1.7 points. At 8,192 roots it is still 18.1 × 10⁻⁵ below the static rule (interval -24.5 to -11.7). The added larger setting was selected in 1 of the 15 training sets.
- **R1 (IQL)** saturates early: 72.7% at 256 roots and between 77.6% and 84.1% from 512 roots on, with no trend. In draw 0 it stays below the static rule at every size (-5.1 × 10⁻⁵ at 8,192 roots, interval -8.0 to -2.2). The wider, longer-trained setting was selected in 6 of the 15 training sets, without a consistent gain. Other draws move the share by up to about ten points, so single-draw differences of that size are not signal.
- **N6 (supervised corrector on fork labels)** is flat from 512 roots on (85.5% to 88.9%) and is not separable from the static rule at any of those sizes.
- In 0 of the 45 learner-by-training-set results, the interval of the difference to the static rule lies above zero.

**2. The support gate sets the smallest usable training set.** It fails in every draw up to 1,024 roots and passes in every draw from 2,048 roots. Rows below the gate show what the learners do there; they are not deployable policies under P8's rules.

**3. This world cannot show a learner beating simple rules, whatever the data size.** The static rule already takes 91.8% of the gap. The room above it is 8.8 × 10⁻⁵, about twice the half-width of a paired comparison on the 6,000 test roots for N6 and R1. P8 used this world to validate the learners' code path, and it serves that purpose. It does not serve as a test of whether learned sequential control pays.

**4. Where room exists (§6).** A hand-built sequential rule reaches the oracle member in the budget world (N4, the DP with an estimated law) and in keep_feedback (N3). Room above every hand-built row is resolved in eval_allocation, interaction, shared_error. Those worlds reward re-measuring a candidate, re-auditing the incumbent, or tracking which recurring keys enable each other. The present learners have none of these actions or state features.

**5. What this suggests for the plan (input to R1-PAPERC-CORE; not a decision).**
- The budget-pacing channel alone is unlikely to carry a claim that learned multi-step control beats hand-built rules: a static rule or an estimated-law DP takes the gap in both budget worlds.
- A learner comparison that can come out either way needs a world, and later a node, where §6 shows room, and learners that have the actions of that channel. The first step would be an E-SYN learner validation in shared_error or eval_allocation with a re-audit or re-measure action.
- The static rule tuned on dev campaigns is the baseline every learned arm has to be reported against.
- A longer curve in this world needs a new seed-registry block; given point 3 it is not worth one.

**Limits.** One synthetic world for the curve. Draw 0 is nested, so its points share data. At most three training draws per size, two at 4,096 and one at 8,192. The intervals cover test roots, not training draws. Grids are small and were not re-tuned per size beyond the declared settings. R1's training steps do not grow with the data except in the one added setting.
