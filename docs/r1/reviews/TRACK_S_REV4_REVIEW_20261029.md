# Review of Track S runbook, revision 4 (29 Oct 2026)

AI-assisted review (fresh agent); read-only; authorizes nothing.

**Scope.** `RB` = rev-4 runbook; `R3` = rev-3 review; `apb`, `h` = snapshots. Spot-checks confirmed: h `snapshot.py`:895–905, apb `features.py`:385, `arms.py`:122–131, `control.py`:16–23, NOISE_FLOOR_COMMON:105–106, LIVENESS_LLAMACPP:78–83, h `langgraph_manager.py`:55–71. Absent from the snapshot: `r1/tracks/schema.py` (RB:125) and PLAN rows R1-TRACKS-HOST/-2.

**Verdict: REVISE.** 2 BLOCKING, 5 MAJOR, 9 MINOR.

## 1. Revision 3 → 4 (body checked)

| Finding | Verdict | Reason |
|---|---|---|
| BL-A | ACCEPT | The primary is a paired total-Y difference (RB:136–138), the hybrid score is gone, and the immediate part is defined with common audit seeds (RB:117). |
| BL-B | PARTIAL | The structure is right: campaign-level, class-restricted, and U_split is descriptive. But B can be reached through a weak π′, the S0.6 guard against that is circular, and the joint power is 64 %, not 80 % (BL-1, BL-2). |
| MA-1 | ACCEPT | Predictive sd, (key, sign) groups, inflation, the gate and the rewording are all in (RB:109–115). Gate details are in mi-4. |
| MA-2 | PARTIAL | Roots run at g₀ and the grid includes h. But "m* by value on dev roots" cannot be carried out as written, and m̃ does not exist until S3b (MA-1). |
| MA-3 | PARTIAL | 200 replications, the placebo and test 5 were added. But the FPR gate fails an exactly nominal test 67 % of the time, the placebo voids the run with probability α, and P1/P2 are tuned to pass (BL-1, BL-2). |
| MA-4 | ACCEPT | Sizing uses `vary` (RB:77, 148). How many S0.5 pairs give σ_D is not stated (MA-3). |
| MA-5 | PARTIAL | Audits are costed and the fallback is symmetric. But the cost formula is inconsistent (mi-2), and the schedule depends on an optimistic σ_D (MA-3). |
| MA-6 | PARTIAL | LB > 0 alone now decides A. But the claim that n gives 80 % power ignores Holm and the IUT (BL-2). |
| mi-1, mi-2, mi-3, mi-5, mi-6, mi-7, mi-8 | ACCEPT | Done in the body (RB:90, 68, 141, 103, 107, 188, 125). |
| mi-4 | PARTIAL | The most frequently edited pair, HIDDEN_UNITS × BATCH_SIZE (10/8 edits; LR only 2), is missing. On breast_w the manager edits `max_iter` and C, not `class_weight` (LIVENESS:78–83). |
| mi-9 | ACCEPT | The wording is adopted. Deciding when "explained by budget alone" applies is not operational (MA-4). |

## 2. BLOCKING

**BL-1. A weak π′ makes route B nearly automatic, and the guard against that is circular.**

RB:10 concedes that δ_dec ≈ 10⁻⁴ is buried in campaign-level fork noise (≈ 10⁴ forks to *test*). *Learning* the sign of f̂(s) faces the same signal-to-noise ratio. At F ≈ 300, a cross-validated ridge shrinks f̂ to near its intercept, so π′ becomes a static rule (D ≈ 0) or noise (D < 0). Both give UB₉₅ < δ_Y, which is B. This is rev-2 BL-3, moved up to campaign level. The guard is circular: P1/P2 parameters "are set so that P1 and P2 have ≥ 80 % power" (RB:167). The synthetic nodes also lack LLM-path divergence, the main source of fork noise.

*Fix:*
- (a) Fix the P1/P2 effects **before** computing power: the oracle continuation-aware gain is exactly δ_Y in campaign Y, over the measured k_n decisions, in a diffuse and a concentrated variant. Match the fork-level sd(Q_exec − Q_skip), k_n and the duplicate rate to a ≈ 30-fork real pilot added to S0.5. F is whatever reaches 80 % power on the diffuse variant. If that F is infeasible, B is declared unavailable in advance.
- (b) B also requires a non-degenerate π′: the S3e flip rate of π\* vs m\* is at least a declared minimum. Otherwise the result is "inconclusive (no learned signal)".
- (c) Word B with the learner: "one step of fitted policy improvement over A2-U at g₀, linear in the declared features, from F forks".
- (d) Strongly consider a primary from a **low-dimensional dynamic family**: a budget threshold g(runs left, proposals left) plus a per-(key, sign) probe bonus, 2–4 parameters, tuned by value on dev campaigns with m\*'s tuning budget. This is the DAC-standard "tuned dynamic vs tuned static" comparison. π′ becomes secondary, with Holm over candidates × nodes.

**BL-2. The pre-declared error-rate arithmetic makes the plan fail by construction.**
- **FPR gate.** With 200 replications, UB₉₅ ≤ 7.5 % needs at most 8 false positives. An exactly nominal 5 % test passes with probability 0.33, and a failure is a STOP (RB:92, 270). *Fix:* fail only if the Clopper–Pearson LB₉₅ of the FPR exceeds 5 % (≥ 16/200). Alternatively, run ≥ 1000 replications and require a point FPR ≤ 6 %.
- **Power.** n = (2.49 σ_D/δ_Y)² gives 80 % per node at one-sided α = 0.05. But A under Holm needs the smaller p ≤ 0.025, which gives 70 % power when only one node has the gain. B needs both nodes, which gives 0.80² = 64 %. *Fix:* use n = ⌈(2.90 σ_D/δ_Y)²⌉ (both targets reach ≈ 80 %), or restate the power honestly.
- **Placebo.** A correct placebo still "fails" with probability α, and a failure voids the run (RB:144, 151). That is R3 MA-3's single-N0 problem again, and 15 pairs give little power. *Fix:* add an exact A/A check (same repetition, D ≡ 0) for determinism. Report the different-repetition placebo as the LLM share of σ_D, and STOP only on a gross failure (|mean D| > δ_Y or p < 0.001).

## 3. MAJOR

**MA-1. The m\* selection cannot be carried out as written, and its noise favours A.**
Scoring each (g, h) grid point by value needs its own on-policy campaigns; one A2-U root trajectory cannot score other prices. m̃ needs Î, which exists only after S3b. And the value-best g₀ depends on W, which comes from the same pilot. *Fix:* fix the order: S0.5 runs at W = cap, and binding shares come from truncation. Then fix W. Then run costed dev campaigns per grid point and set g₀ = m\*'s g. Then run S3a. Then select m̃ on dev campaigns. Give m\* at least π′'s tuning data, and use dev seed blocks disjoint from S3a and S3e.

**MA-2. A and B can both hold, and the plan says nothing about precedence.** At tabular n ≥ 155, a gain of 0.3 δ_Y can give LB > 0 while UB < δ_Y on both nodes. A framing switch to route A on a gain the paper itself calls negligible is not defensible. *Fix:* declare "A requires LB > 0 and not B", and word an A ∧ B outcome as "a detectable but sub-margin gain" (B framing).

**MA-3. σ_D comes from an unstated number of pairs, and 0.01 is optimistic.** Under `vary`, σ_joint is 0.010–0.012 per run, and divergent LLM paths add spread. At σ_D ≈ 0.02 with the corrected multiplier, n ≈ 310 for digits and ≈ 840 for tabular, about 100k calls on tabular, which hits the 4-day fallback. With 10 pairs, the 95 % CI on σ_D spans 0.69–1.83×. *Fix:* ≥ 20 S0.5 pairs with sizing on the 80 % upper confidence limit of σ_D, or a blinded re-estimation of sd(D) at n/2. Declare n_max per node, with "B unavailable" if n_max < n. Add a σ_D = 0.02 row to the cost table.

**MA-4. π′ must nest m\*, and the feature set is not pinned.** `r1/tracks/schema.py` is absent. Without the A2-U index (1 − π)V(t*) and the E2 margin m̂ as features, π′ cannot express m\*. *Fix:* list the features in S0.7 and add a fixture test: penalising everything but the index reproduces A2-U at some g.

**MA-5. "Explained by budget alone" (RB:28) has no test.** Δ_B at the forks is underpowered (R3 BL-B). *Fix:* add a declared S3e secondary, π′ refit without budget features. Use the budget wording if that candidate's gain does not exclude 0 while the DP candidate's gain does not differ from π\*'s.

## 4. MINOR

- **mi-1.** `manager_seed` is keyed on `campaign_id` (h `langgraph_manager.py`:55–71). π\* and m\* runs of one instance must share an instance-level key, or the pairing is lost. Name four disjoint seed blocks (S0.4, S0.5/dev, S3a, S3e) and a separate S3e audit-seed block.
- **mi-2.** Cost formula (RB:238): "2/3 × 2 × 2" gives 4.67 leaves per fork, not 3.3. The exec/skip r = 2 on the channel third and the E2 leaves are also missing, so the count is about 4 per E1 fork plus E2.
- **mi-3.** S1.1 pairs: see the mi-4 row in §1.
- **mi-4.** Calibration gate: stratify coverage by prior group count (0, 1–2, ≥ 3); include audit noise in the interval; require ≥ 100 predictions; define the S0.5 roots' "declared g".
- **mi-5.** State whether KG verify is on. D1″'s "never fires" holds only at g = 0.1 σ_node, and grid prices below that can fire it and spend 2r runs.
- **mi-6.** Name the deployed π′: a full-data refit or the fold average, the λ rule, and its sha256.
- **mi-7.** The fallback is decided only from S0.5 projections, before S3a. Pre-emption pauses a node and never drops it after outcomes exist.
- **mi-8.** State one-sided 95 % t-intervals for LB and UB.
- **mi-9.** Secondary candidates are exploratory and cannot move the route. Cut U_split and S3c (over-engineering). Keep the channel arms, S4a and S1.1.

## 5. Notes

- **Leakage.** Once mi-1 and MA-1 are fixed, fresh S3e instances leave no winner's curse. What remains is selection noise, which favours A through a mistuned m\* (MA-1).
- **Two hosts.** The split is valid.
- **DAC lens.** Call π′ "one iteration of rollout-based approximate policy iteration". BL-1(d) is what a DAC reviewer expects. The instances are seeds of one node.

## 6. What blocks acceptance

1. **BL-1:** S0.6 effect sizes fixed in advance at δ_Y and matched to a real fork-noise pilot. A non-degeneracy condition on π′ for route B, and B worded with the learner and F. (Or BL-1(d).)
2. **BL-2:** an FPR gate that a nominal test passes, an n that powers Holm and the IUT, and a placebo that cannot void the run by chance.

Settle MA-1 (operational m\* selection and order) and MA-3 (σ_D sizing, n_max) in the same revision. Together they decide whether tabular stays in the decision.
