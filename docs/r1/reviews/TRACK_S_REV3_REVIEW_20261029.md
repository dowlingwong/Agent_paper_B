# Review of Track S runbook, revision 3 (29 Oct 2026)

AI-assisted review (fresh agent); read-only; authorizes nothing.

**Scope.** `RB` = `TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md` (rev 3); `R2` = rev-2 review; `apb` = `snap/apb`; `h` = `snap/harness/src/autoresearch/`; `T4rev` = `apb/docs/r1/proposals/T4_PROP10_REVISION_20261028.md`; reports under `apb/docs/r1/reports/`. PLAN rows R1-TRACKS-HOST / -2 are absent from the snapshot PLAN and were not verified.

**Verdict: REVISE.** 2 BLOCKING, 6 MAJOR, 9 MINOR.

## 1. Revision 2 → 3 (body checked)

| Finding | Verdict | Reason (body) |
|---|---|---|
| BL-1 | PARTIAL | A2-U is declared, labelled "not the deployed rule", P1 sits on a shared key, and A2 is descriptive (RB:101–107, 168). But the model is misspecified in ways that break the "theorem's myopic rule" claim (MA-1). |
| BL-2 | PARTIAL | Raw units (RB:109), π′ without g (RB:127), budget-only wording (RB:150): done. The new hybrid score creates a worse problem (BL-A). The static comparator is not the best static rule, and E2 has no static offset (MA-2). |
| BL-3 | PARTIAL | U_split, ≥ 30 instances, cross-fitting with a refitting bootstrap, and N0 at non-binding W are all present (RB:128–138, 170, 199). But U_split does not close the escape, is not unbiased under frozen noise, and the sizing is infeasible (BL-B). |
| MA-1 | ACCEPT | W from S0.5, and "not binding" is a finding (RB:191–192). |
| MA-2 | ACCEPT | Δ_I and Δ_F relabelled; per-trial-seed check cut (RB:216–217, 236). |
| MA-3 | PARTIAL | Hook and four invariance tests added (RB:88, 93–97). The real-node budget control has no pass criterion and is underpowered; N0 is a single realisation (MA-3). |
| MA-4 | PARTIAL | Per-host latency, one node per host, third-of-forks, fallback: added. The illustrative F = 600 is 15–40× below what the declared margins imply. Audits are not costed (MA-5). |
| MA-5 | ACCEPT | δ_Y = max(0.002, 0.5 σ_node), declared in raw units (RB:112). Its noise basis is fixed-split (MA-4). |
| MA-6 | PARTIAL | S3d has a rule (RB:224–227), but its power statement is impossible (MA-6), and the static baseline is not tuned by value. |
| mi-1 | ACCEPT | U cut (RB:236). |
| mi-2 | PARTIAL | Holm levels are attached to "first/second node", not to the p-value order (RB:141). |
| mi-3 | ACCEPT | RB:31. |
| mi-4 | ACCEPT | Pooled with an indicator, and k_n sums E1 and E2 (RB:113, 128, 132). Interactions are unspecified (mi-8). |
| mi-5 | ACCEPT | `vary` declared (RB:87); §1 corrected. The raw-unit departure from PLAN:118 is undeclared (mi-6). |
| mi-6 | ACCEPT | RB:174. |

## 2. Spot-check of RB §1

| Claim | Verdict | Evidence |
|---|---|---|
| D6: A2 is constant per node | Confirmed | apb `r1/c3/arms.py`:122–131; `control.py`:218–226 |
| D1: W and the cap bind | Confirmed | `control.py`:170–183, 351–363; PLAN:118–121 (Y "normalised per node", PLAN:118) |
| D1″: KG verify never fires | Confirmed | `control.py`:16–23; h `campaign.py`:718–740 (2r runs) |
| D2: no E2 keep/discard action | Confirmed | h `campaign.py`:429–433; `controller.py`:264–270 |
| H1′: budget index and LLM seed | Confirmed. The seed has a `repetition` argument, so r = 2 is supported | h `langgraph_manager.py`:55–71, 122–141; `budget.py`:24–25 |
| H3: seen-set grows only from executed rows | Confirmed | apb `features.py`:390–391, 405–411, 423 |
| H4: no override hook | Confirmed | h `snapshot.py`:702–709, 836–848, 895–905, 976–982 |
| H6: one parameter per proposal | Confirmed | h `llm/providers.py`:23–27 |
| B2: σ_node, fixed split | Confirmed. Under `vary`, tabular σ_split is 0.0123 against σ_train 0.0029 | NOISE_FLOOR_COMMON_20261022:105–106 |
| B5, B6, H4′ | Confirmed | LIVENESS_LLAMACPP_20261026:76; LLAMACPP_PROBE_DT_20261025:16–17 |

## 3. BLOCKING

**BL-A. The primary score is not a policy value, and it can credit a harmful policy.**

Y telescopes as Y = Y_s + I_a + C_a, with I_a the immediate part. RB:117–121 replaces I_a by the forecast V̂*_a and keeps the measured C_a. Hence

E[score(a,s)] = Q_a(s) − (E[I_a|s] − V̂*_a(s)).

I_a and C_a are coupled through the incumbent. A bad keep (I < 0) is typically followed by recovery (C > 0); trial-1 recovery, RB B5, is the same mechanism. Example: E[I] = −0.010, V̂* = +0.001, recovery ΔC = +0.008. The true ΔQ is −0.002, but the score gives +0.009. Ĉ learns "execute here", and route A fires on a policy that lowers Y. S3d protects only the DAC headline, not the route-A claim. Also, "measured immediate part" is never defined (RB:121).

*Fix.*
- Make the primary a **nested comparison on total measured Q**: π′ = argmax[Î + Ĉ] against m̃ = argmax[Î − ĝ]. Î is a cross-fitted immediate-value model with the same features and capacity. Both are scored on total Q, so one-step heterogeneity is available to both and credited to neither.
- Define I = 1{kept} × the fresh-seed audited increment over the branch's own incumbent, with common audit seeds. Only these are artefact-free (DI_TEST_MEMORY_ON_PARTIAL_20261019:129–133).
- Keep the forecast-score as a secondary.

**BL-B. Route B is neither sound nor reachable.**
- **U_split does not bound the achievable gain.** It is the value of a one-sample plug-in rule. With heterogeneous advantages A(s) around the static rule and per-fork noise σ_d ≫ |A|, E[U_split] ≈ E[A²]/(σ_d√(2π)). Take A = ±3 δ_dec at *every* fork, σ_d = 0.01 and δ_dec = 1.3×10⁻⁴. Then E[U_split] ≈ 3×10⁻⁶ ≪ δ_dec, so B passes while a gain of ≈ 3 δ_Y per campaign is available. The escape is not closed.
- **"Unbiased under the null" (RB:138) needs repetitions that are independent given the fork.** Repetitions differ only in the LLM seed. They share the fork's executed run (same configuration, frozen worker seed; H4′) and all frozen worker noise, so choosing on repetition 1 selects on shared noise.
- **Power is infeasible.**
  - Take k_n ≈ 22–28: about 13–19 eligible E1 decisions, plus E2 decisions at W ≈ 10 (B2; DUPLICATE_RATE_PILOT_20261022:28–30). Then δ_dec ≈ 0.0033/25 ≈ 1.3×10⁻⁴ (digits) and 0.002/25 ≈ 8×10⁻⁵ (tabular).
  - F ≈ (2.49 σ_d/δ_dec)² gives ≈ 9k–23k forks for σ_d = 0.005–0.008, against the illustrative 600 (RB:259). That is 1–2.4 M calls per node.
- **The real-node budget control will likely fail.** Δ_B ≈ P(bind) × (value of the marginal run), which is ≈ 0.5 × O(g) ≈ 3×10⁻⁴. With SE ≈ σ_d√2/√(F/3), the control is not detectable at the planned F. Its failure makes B "unavailable" by design (RB:149).

Net effect: the outcome is pre-committed to A-or-inconclusive.

*Fix.*
- Move the route-B test to **campaign level and restrict it to a class**: online paired equivalence of π′ against the tuned static rule, UB₉₅(Y(π′) − Y(m_ĝ*)) < δ_Y on fresh instances. This is the same machinery as S3d, run in both directions. At sd ≈ 0.01 and δ_Y = 0.0033 that is n ≈ (2.49 × 0.01/0.0033)² ≈ 57 paired instances, about 5k calls.
- Word B as "no gain ≥ δ_Y from continuation-aware re-thresholding within Π_Ĉ".
- Make U_split descriptive, or drop it.
- Give Δ_B a stated pass criterion and power it at the S0.5 effect size, or replace it with a mechanical check (W = 1 or 2, where Δ_B is large).

## 4. MAJOR

**MA-1. A2-U is not "the theorem's" Bayes-myopic rule.** Prop. 10(a′) needs the true posterior given O_n (T4rev:63, 95). The model in RB:101–105 has four problems:
- (i) τ_n, the posterior sd of the key *mean*, is used as the proposal's prior sd. The predictive sd should be √(τ_n² + τ_w²). The rule becomes overconfident, and V* collapses after a few executions.
- (ii) The update pools edit directions and step sizes per key, although increments on one key change sign.
- (iii) Observations within an incumbent spell share the incumbent's error and the frozen noise (T4rev:171–180), so they are not independent.
- (iv) The prior comes from execute-all campaigns, whose proposal law differs (NF-a). RB:89's "fitted on the proposals it will see" is therefore false.

On the MLP nodes the manager edits three keys (LIVENESS_LLAMACPP_20261026:78–79), about 5 executions per key per campaign, so (i)–(iii) bite fast. Misspecification then appears as a spurious Δ_I.

*Fix.*
- Use a hierarchical normal model with predictive variance, indexed by key × sign of the step.
- Inflate the observation variance for within-spell correlation.
- Add an S0.5 calibration gate: coverage of 80 % predictive intervals for the next same-key audited Δ, with a declared tolerance.
- Reword RB:107 as "a Bayes-myopic rule under a declared model".

**MA-2. The comparator is not the root policy and not the best static rule.**
- Roots and continuations run at the declared g (RB:199), but the comparator uses ĝ_fold. The offline contrast is therefore Q^{m_g}(s, π′) − Q^{m_g}(s, m_ĝ), not V(π′) − V(m_ĝ). The policy-improvement step is relative to m_g only.
- ĝ = −mean(ΔC) (RB:126) is not the value-maximising static price, and its IPW weighting is unstated.
- E2 has no static offset, so any mean keep-channel effect is credited to π′.

*Fix.*
- Run roots at a pilot price ĝ₀ from S0.5, so that root and comparator coincide.
- Choose ĝ (and an E2 offset ĥ) by maximising cross-fitted IPW value on a grid.
- For S3d, tune the static g by value on dev instances. This is the DAC "best static" baseline (Biedenkapp et al. 2020; Adriaensen et al. 2022, JAIR).

**MA-3. The estimator's error rates are not calibrated.**
- The refitting cluster bootstrap with cross-fitting must put duplicated clusters in the same fold.
- 1{π′ ≠ m} is non-regular near the null.
- A single N0 run voids everything with probability ≈ α.

*Fix.*
- The synthetic controls are cheap, so replicate N0 (≥ 200 runs) to show a route-A false-positive rate ≤ α and nominal coverage. Replicate P1 and P2 for power.
- Add a real-node placebo: treat the two same-action repetitions as pseudo-arms, and require I_seq to be null.
- Add invariance test 5: post-fork worker seeds are keyed by trial, identical across arms, and the workspace is restored after ghost runs.

**MA-4. The noise basis is fixed-split, but Track S runs `vary`.** The σ_node values (RB:76, 112, 165–166) are fixed-split. Under `vary`, tabular's split sd is 0.0123 (NOISE_FLOOR_COMMON_20261022:106), so "lower noise" for Primary 2 is unsupported. σ_d, fork sizing and synthetic matching must use the S0.5 `vary` measurements. The margins can stay as substantive choices.

**MA-5. Cost and schedule.**
- F must be recomputed (BL-B).
- The cost model counts LLM calls only. Each leaf also needs K = 5 audits for Y and K for I (BL-A), × r × arms.
- S0.3 is large (a forced E2 keep is a new action, D2; the hook; three arms; A2-U; synthetic nodes; analysis) for 4–5 agent-days plus review. A 14–17 Nov decision is not credible.
- The fallback drops tabular even when TASL-2, the digits host and Track X's host, is the bottleneck.

**MA-6. The S3d and route-A rules carry a point-estimate condition that caps power.** With "Ŷ ≥ δ_Y and LB > 0", power is ≤ 50 % at a true effect of δ_Y, so "80 % at δ_Y" (RB:227) is impossible. The same holds for Î ≥ δ_dec (RB:141). *Fix:* power at 2δ_Y, or use LB > 0 alone, with δ only for the wording.

## 5. MINOR

- **mi-1.** S0.4 and S0.5 list "zhixu portal" (RB:89–90), but tabular runs on TASL-7 (RB:182, 247).
- **mi-2.** S0.4 runs "at the S3 regime", but W is set in S0.5, which needs S0.4's prior. Declare S0.4 at a non-binding W (= cap).
- **mi-3.** The existing `budget_frac_left` is trial-indexed, 1 − (b−1)/runs_total (apb `features.py`:257, 385). At cap 40 and W = 10 it goes negative and is identical in skip and ghost. Define "runs left" from `worker_runs_remaining` (h `budget.py`:112).
- **mi-4.** S1.1 tests MAX_ITER × LR (RB:185), but the manager edits HIDDEN_UNITS, BATCH_SIZE and LR (LIVENESS:78–79). Test those pairs.
- **mi-5.** Holm order is by p-value. Give Δ_B's pass criterion.
- **mi-6.** Declare raw-unit Y as a departure from PLAN:118 in S0.2.
- **mi-7.** The oversample is centred at |V̂* − g| ≤ b (RB:202), but flips occur near ĝ or −Ĉ. Centre it at ĝ₀.
- **mi-8.** Specify whether Ĉ has E1/E2 interactions or only an intercept shift.
- **mi-9.** For a DAC reader, a budget-dependent threshold *is* DAC. Word it "a dynamic-knapsack threshold explained by known OR theory" rather than "not DAC". Note too that the instances are the seeds of one node: say so before any cross-task claim.

## 6. Notes

- **Two-host split.** Valid: no node's table mixes hosts, and cross-node comparisons are descriptive. Route B's "both nodes" requirement makes it hostage to the slower host.
- **Over-engineering.** U_split, the IPW oversample, Holm plus the intersection–union test over two nodes, and S3c can shrink once B moves to campaign level. Keep the ghost and controller-only arms (attribution), S4a, and the replicated synthetic controls (estimator calibration).

## 7. What blocks acceptance

1. **BL-A:** a primary on total measured Q, with a nested immediate-only comparator and a defined, audited immediate part.
2. **BL-B:** a route-B test that bounds the achievable gain and is feasible: the class-restricted campaign-level equivalence, or an explicit statement that B is unreachable. Plus a powered, defined budget control.

Settle MA-1 (A2-U predictive variance and calibration gate) and MA-2 (root = comparator, value-tuned ĝ) in the same revision; both change what I_seq means.
