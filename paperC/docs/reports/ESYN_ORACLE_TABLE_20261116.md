# E-SYN worlds and certified oracle gains (build runbook P3; BUILD_LIST B3 + B17)

**AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.** Synthetic worlds are implementation checks
and oracle gaps; they are never evidence about the real loop (plan §5).

- **Data:** `paperC/esyn/oracle_table_v1.json`, produced by `python -m paperc.esyn.table` (about 7 minutes on one
  CPU).
- **Tests:** `paperC/tests/test_esyn_p3.py`, plus `test_esyn_worlds.py` for the pinned port. The suite has 122
  passed and 1 expected failure (information's certification, §4).

## 1. What was built

| Module | Content |
|---|---|
| `esyn/worlds.py` | Track S world mechanism, ported unchanged from `trackS-ops-20261030` @ `fab88fc` and tested against the pinned original (steps 1–2) |
| `esyn/extra.py` | `ESynWorld`: a Track S world plus Paper C's declared data: channel, declared gain sign, discrete size law, interaction matrix, comparison model (`increment` or `config`), offered epochs; the registry of 7 worlds (step 3) |
| `esyn/sim.py` | the campaign simulator: Paper B's loop as Track S runs it (one proposal per slot, rule skips, trial 1 executed and kept, E1/E2, W and llm_cap), plus `verify`, `reaudit` and `final`; writes `spt_transition/v1` rows that `check_campaign` accepts, with propensity replay and the seed registry (step 6) |
| `esyn/policies.py`, `esyn/families.py` | static rules (Paper B's class) and channel families: DP thresholds; budget-, keep- and novelty-dependent rules; interaction-aware keep; evaluation allocation |
| `esyn/dp.py` | exact backward induction for the budget world: (slot, runs left) with a discrete V\* law; the exact value of every static threshold (step 4) |
| `esyn/oracle.py` | certified oracle after Track S `oracle.certify`: best static and best member chosen on a selection block; paired evaluation on a disjoint block, sized to a 95 % half-width ≤ 5 % of the planted gain (step 5) |
| `schema.py` | optional `State.candidates` on `final` rows; the selection must be one of them (the B17 item the P1 schema deferred) |

## 2. Worlds

| World | Channel on | W | Comparison | Epochs | Mechanism |
|---|---|---|---|---|---|
| strict_null | none | 40 (not binding) | increment | E1, E2 | fresh keys, discrete sizes; the myopic Bayes rule is optimal |
| budget | budget | 8 | increment | E1, E2 | as strict_null, but about 18 executable proposals compete for 8 runs |
| interaction | incumbent interaction | 40 | increment | E1, E2 | 4 recurring keys; pairs (0,1), (2,3) complement by 0.012: the first kept key of a pair adds M to its partner's later increment |
| shared_error | shared incumbent error | 60 (not binding) | config | E1, E2, reaudit | a kept candidate's recorded value carries its selected measurement error into every later comparison until re-audit |
| eval_allocation | evaluation control | 40 | config | E1, E2, verify, reaudit, final | verify, re-audit and final selection under the shared-error model; extra measurements cost runs |
| information | information (Track S P1-diffuse) | 10 | increment | E1, E2 | probes open keys whose size-16 follow-ups are large and noisy (strength 16, as Track S's S0.6 grid) |
| keep_feedback | keep feedback (Track S P2+-diffuse) | 10 | increment | E1, E2 | an early keep raises the θ mean of the next proposals (strength 0.012, Track S's grid) |

**Measurement model.** In `config` worlds each run measures a configuration with sd σ_cmp/√2, so a single paired
comparison has sd σ_cmp. The loop compares the candidate's mean measurement with the incumbent's recorded mean.

**Belief model.** A2-U's keyed conjugate model (Track S).

**Campaign value.** Y = true value of the final configuration minus y0, with no audit noise.

## 3. Oracle table (5 % tolerance; selection block 2,000 campaigns, pilot 1,000, n_max 200,000)

| World | Channel (declared sign) | W | Best static (selection) | Best member (selection) | Planted gain (source) | Oracle gain ± 95 % hw | Tolerance | n | Certified |
|---|---|---|---|---|---|---|---|---|---|
| budget | budget (+) | 8 | `static:0.001,0` | `dp` | 0.00211 (declared) | +0.00217 ± 0.00010 | 0.00011 | 11156 | yes |
| eval_allocation | eval_allocation (+) | 40 | `static:0,-0.001` | `evalloc:0,-0.001,1,2,2,incumbent` | 0.00343 (selection) | +0.00344 ± 0.00016 | 0.00017 | 8175 | yes |
| information | information (+) | 10 | `static:0.0015,0.001` | `dynamic:0.002,0,0,0,0,0.002,0.01` | 0.00107 (selection) | +0.00105 ± 0.00026 | 0.00005 | 200000 | no |
| interaction | interaction (+) | 40 | `static:0,0` | `interaction:0,0,0.25` | 0.00116 (selection) | +0.00116 ± 0.00005 | 0.00006 | 27942 | yes |
| keep_feedback | keep_feedback (+) | 10 | `static:0.0005,-0.003` | `dynamic:0.0005,-0.002,0,0,0.008,0,inf` | 0.00277 (selection) | +0.00237 ± 0.00013 | 0.00014 | 11164 | yes |
| shared_error | shared_error (+) | 60 | `static:0,-0.001` | `evalloc:0,0,0,1,3,incumbent` | 0.00213 (selection) | +0.00211 ± 0.00010 | 0.00011 | 18832 | yes |
| strict_null | none (0) | 40 | `static:0,0` | `dynamic:0,0,0.1,0.004,0,0,inf` | 0.00660 (floor) | +0.00000 ± 0.00000 | 0.00033 | 1000 | yes |

**Reading the columns.** The best member is the selection-block winner of the world's family. Its gain is
measured on the evaluation block against the best static rule, on paired campaigns.

**Planted gain:**
- "declared" is the exact DP gain;
- "selection" is the member's selection-block gain;
- "floor" is the absolute tolerance used for the strict null: 5 % of σ_cmp.

**Exact DP (budget world):**
- DP value 0.01139 against the selected static's exact value 0.00928 (g = 0.001, which executes only the largest size).
- Exact gain 0.00211; the oracle measures 0.00217 ± 0.00010.
- On the evaluation block, the DP policy's simulated mean is 0.01159, within the half-width plus tolerance of the
  exact value.
- In strict_null, the DP equals the static rule g = 0 exactly: the gain is 0 to machine precision, because W does
  not bind.

**Strict null:** the selection winner (`dynamic:0,0,0.1,…`) makes exactly the static rule's decisions, so the
measured gain is exactly 0. All 15 members that decide differently are worse on the selection block; the best of
them, `dynamic:0,0.001,0,0.004,0.002,…`, is at −0.00051 ± 0.00009 (se).

## 4. Findings (E-SYN only)

1. **Every declared channel shows a positive oracle gain** (lower 95 % bound > 0). Six of seven worlds are
   certified at 5 % precision.
2. **Information is positive but not certified.**
   - The tau-gated novelty member gains +0.00105 ± 0.00026 at n = 200,000.
   - P1's size-16, σ = 0.05 follow-ups make campaign values so noisy that 5 % precision would need about 5
     million paired campaigns.
   - Track S's analysis notes found larger gains with a 9-threshold schedule. Porting that schedule as a member is
     open.
3. **Evaluation control pays only when runs are not too scarce.** These are calibration runs on 1,000–1,500
   selection campaigns, not in the table:

   | World | W | Best evaluation-control member minus best static |
   |---|---|---|
   | shared_error | 24 | −0.0012 |
   | shared_error | 60 | +0.0021 (certified) |
   | eval_allocation | 24 | no member beats the static rule |
   | eval_allocation | 32 / 40 / 60 | +0.0012 / +0.0036 / +0.0053 |

   So re-audit and verify buy accuracy with runs, and the oracle gain depends on W.
4. **The best static rule compensates part of the winner's curse.** In both config worlds it uses h = −0.001, below
   the Bayes threshold 0: it lowers the keep bar against an inflated incumbent record. The evaluation-control
   members beat it anyway.
5. **Keep feedback.**
   - The best static keeps very liberally (h = −0.003).
   - The member's budget-dependent keep threshold adds +0.0024.
   - The selection gain (0.0028) shrank on the evaluation block (0.0024), the usual winner's-curse shrinkage of
     selecting among 24 members.

## 5. Deviations and choices to review

- **Schema.** `State.candidates` is added to `spt_transition/v1` as an optional field, with two row rules. Older
  rows stay valid, and a test covers this. This is a change to the accepted P1 schema.
- **Members around the best static.** Member families cross the channel parameters with the static thresholds one
  grid step around the best static rule. They are built after that rule is chosen, on the same selection block.
  Members equal to a static rule are excluded by construction, except where a channel parameter has no effect;
  that happens in the null, and is reported.
- **Tolerance floor.** The strict null uses an absolute tolerance of 5 % of σ_cmp, because its planted gain is 0.
- **Resizing.** After the pilot, n is re-sized from all draws so far, with a 10 % margin, at most 3 times. Budget
  needed one round, after the pilot-based n fell just short.
- **Track S worlds.**
  - information and keep_feedback use Track S's analysis-grid strengths, not the S0.6 values the collector's
    controls used. The simulator is Paper C's own; only the world mechanism is the pinned port.
  - The first calibration gave negative gains for four worlds. It had two faults: wrong strengths (P1 0.02, P2+
    0.004), and member grids that lacked the best static rule's own thresholds. The strengths were corrected from
    Track S's notes and the families were rebuilt around the best static. Two budgets were also changed, for the
    reason in §4.3: shared_error 24 → 60 and eval_allocation 24 → 40. The null and the channel mechanisms were not
    changed.
- **RNG.** Every campaign's generator is keyed `[60001, world code, instance]` (`paperc_rng_keys`).
  - Recorded campaigns use instance seeds 50000 + i and audit seeds from 10,000,000.
  - Oracle blocks use instances 1,000,000 + i (selection) and 2,000,000 + i (evaluation); these enter only the RNG
    key.
- **Not yet in E-SYN.** Track S P0 and P2−: Track S found no gain ≥ 1 δ_Y there. Pairs of channels. Fork designs (P6).

## 6. Next

- P4: the policy interface and the non-RL ladder on these worlds, with B18's sequential-testing comparators.
- The information member (a ported schedule) is an open item for P3's extension.
