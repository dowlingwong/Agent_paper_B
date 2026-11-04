# Review of Track S runbook, revision 2 (29 Oct 2026)

AI-assisted review (fresh agent); read-only; authorizes nothing.

**Scope.** Runbook and rev-1 review from the working tree; planning docs and `r1/` code at `docs/c3-pool-28oct` (`cefa389`); harness `r1` (`897d83c`).

**Citations.** `RB` = `docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`; `apb` = this repo at `docs/c3-pool-28oct`; `h` = `autoresearch_harness@r1:src/autoresearch/`; `T4rev` = `docs/r1/proposals/T4_PROP10_REVISION_20261028.md`; reports are under `docs/r1/reports/`.

**Verdict: REVISE** — 3 BLOCKING, 6 MAJOR, 6 MINOR.

## 1. Rev-1 resolutions (RB §11)

| Finding | Verdict | Reason |
|---|---|---|
| B1 | PARTIAL | Continuation framing and arm differences adopted. But "keeping the myopic one-step estimate denies miscalibration credit" fails: under A2 that estimate is a constant (BL-1), I_seq scores total measured Q where π′ flips, and the run cost is counted twice (BL-2). |
| B2 | PARTIAL | Cross-fitting, uniform forks and IPW are in. The E1 near-threshold oversample and the \|V*−g\| feature are degenerate under A2 (BL-1); the number of instances (clusters) is never stated. |
| B3 | PARTIAL | One primary, a symmetric A/B rule and voiding controls, yes. But rev-1 B3(a) recurs: I_seq still contains the budget channel, which RB:148–151 calls an OR fact; route B passes when π′ rarely flips (BL-3); "inconclusive" wording still leans to B (mi-3). |
| M1 | ACCEPT | c = 1 dropped, D1″ rewritten. (D1″ is moot in practice; see fact table.) |
| M2 | PARTIAL | Arms exist, but under A2 Δ_I is only the duplicate filter, Δ_B ≡ 0 unless W binds, and Δ_F mixes NF-a with NF-b (MA-1, MA-2). |
| M3 | PARTIAL | P2 is sound. P1 cannot pass with an A2 continuation (BL-1). No control exercises the LLM path (MA-3). |
| M4 | PARTIAL | Y-unit margin and different-seed null adopted. Margin inflated by trial-1 recovery, Y normalisation undefined, 300 forks not derived (BL-3, MA-5). |
| M5 | ACCEPT | Route B is worded as empirical. The per-trial-seed check is mis-targeted (MA-2). |
| M6 | ACCEPT | DP restated, offline only, S2b conditional. |
| M7 | PARTIAL | S3c added conditionally. U as defined cannot fall below δ_dec (mi-1). A label-table simulator cannot represent feedback (MA-6). |
| Per-call identity | ACCEPT | Per call, serial, 100 %. |
| A/A test | ACCEPT | Covers the myopic action only; arm-invariance tests are missing (MA-3). |
| Trial 1 | ACCEPT | Forks exclude trial 1; the margin does not (MA-5). |
| Stronger manager | ACCEPT | — |
| Duplicate horizon | ACCEPT | — |

## 2. Fact-check of RB §1

| Claim | Verdict | Evidence |
|---|---|---|
| D1 hard budget | Confirmed | apb `r1/c3/control.py`:170–183, 351–363; PLAN:118; `r1/c3/offline_eval.py`:23–28 |
| D1′ toy (2.5 vs 2.25) | Confirmed by own arithmetic | — |
| D1″ verify spends 2r runs | Correct, but overstated as a reason W binds: the Track S controller's KG verify "never fires" at g = 0.1 σ_node, r = 2 when σ_cmp ≤ σ_node | h `control_plane/campaign.py`:718–740; apb `control.py`:16–23 |
| D2 action sets | Confirmed. E2 has no keep/discard action, so a forced keep is new code | h `campaign.py`:429–433; `control_plane/controller.py`:264–270 |
| D3, D5, B1′ | Confirmed | apb `r1/c3/env.py`:8; TRACK_P:153–157, 386; DI_TEST_MEMORY_ON_PARTIAL_20261019:127–133; `theory/T4_FEEDBACK_PROPOSER.md`:125 |
| H1 | Confirmed; only `one_line/v1` is declared | h `memory/summarizer.py`:27–51, 100–103 |
| H1′ | Confirmed. The shown "budget index" is consumed trials + 1, so skip and ghost share it and the LLM seed | h `manager/langgraph_manager.py`:55–71, 122–141; `control_plane/budget.py`:24–25 |
| H3 | Confirmed | apb `r1/c3/features.py`:390–391, 402–411, 423 |
| H4 | Partly. `resume_campaign` takes first_action, policy, horizon, worker, manager, keep_prior only: no arm-override hook. The replayed E1 run is debited and its configuration enters the harness novelty set | h `control_plane/snapshot.py`:895–905, 836–848, 976–982 |
| H4′ | Confirmed; the probe compared 3 serial requests only | LLAMACPP_PROBE_DT_20261025:17 |
| H5 "≈12 runs, 23–44 s per leaf" | Unsupported: the cited file holds only the budget dataclasses; the path is `control_plane/budget.py` | h `control_plane/budget.py`:10–125 |
| B1 one-parameter schema | Line off: the schema is at h `llm/providers.py`:23–27 | — |
| B2 σ_node, 727/841, δ_n | Confirmed. Both MLP nodes' D21 split policy is `fixed`, not `vary`; breast_w σ_joint is 0.0038 | NOISE_FLOOR_COMMON_20261022:105–107; DUPLICATE_RATE_PILOT_20261022:33 |
| B2 "7–10 informative decisions" | Stale for cap 40: the duplicate share rises with campaign length | DUPLICATE_RATE_PILOT_20261022:28–30, 38 |
| **Omitted, decisive** | The Track S myopic controller (A2) forecasts one constant per node for every non-rule proposal | apb `r1/c3/arms.py`:10–12, 122–131; `control.py`:221–226 |

## 3. BLOCKING

**BL-1. The base controller cannot use information, so the information channel and P1 are untestable as designed.**

A2 is a constant (π, μ, τ) per node plus rule skips (`arms.py`:10–12, 122–131). E1 executes iff (1−π)V(t*; μ, τ, σ_cmp[kind]) ≥ g (`control.py`:221–226). Consequences:
- V*_n is constant per (node, edit kind). The myopic E1 action is the same for every non-rule proposal, so E1 forks only ever test one direction of deviation. If that action is "execute" (the non-degenerate case), Prop. 10(c)-type deviations, executing what myopic skips, never occur. The E1 oversample (RB:162) and the \|V*−g\| feature (RB:190) are degenerate.
- The forecaster ignores history. A one-step deviation followed by the A2 continuation therefore cannot cash in information; 10(c)'s gain needs a Bayes-updating continuation (T4rev:139–140, 167). I_seq has no power for NI, and Δ_I reduces to the duplicate filter.
- **P1 cannot return A** unless it runs another controller, which would void it as a pipeline check. Under RB:108 route B is then unavailable by design.

*Fix.* Declare one option:
- (a) A Bayes-updating base controller for Track S (e.g. A2 plus a per-key conjugate update from executed Δ̂), stated as not the deployed rule.
- (b) Keep A2; drop P1 and NI from the route-B conditions, and word route B as covering budget and feedback only. To test NI, add a two-step deviation arm: execute a probe, then decide the next same-key proposal with its result.

**BL-2. I_seq is not on one scale and still credits non-sequential effects.**
- π′ uses (V̂* − g) + Ĉ(s) (RB:97). Ĉ is fitted on measured continuations, which already contain the run's opportunity cost, so −g counts it twice. RB:87 says g enters no outcome; it enters π′.
- V̂* and g are in metric units (`control.py`:40–42); Y is "normalised per node" (PLAN:118) with no formula found anywhere.
- I_seq scores total measured Q at flipped forks. With a constant one-step estimate (BL-1), any correlation between Ĉ's features (trial index, keeps, key seen) and the true immediate value selects flips where that value is low. One-step heterogeneity then earns credit.
- The budget channel sits inside the primary, although RB:148–151 calls it OR, not DAC, evidence.

*Fix.*
- State Y in raw metric units.
- Define π′ as: execute iff V̂* + Ĉ(s) > 0.
- Benchmark π′ against the myopic rule at a static g re-fitted on the training fold (g_fold = −mean Ĉ). This is the DAC "best static configuration" baseline.
- Make the primary the continuation-only contrast at flipped forks, E_w[1{π′ ≠ m_g}(C_π′ − C_m_g)]. Keep total-Q I_seq as a secondary.
- Declare in advance how a budget-only route A is worded (e.g. "budget-coupled threshold, not DAC").

**BL-3. Route B has an escape route and is not powered.**
- I_seq is 0 wherever π′ = m: a heavily regularised Ĉ that rarely flips yields route B by construction.
- δ_dec = δ_Y / k_n is a per-decision margin, but each fork's contrast carries the noise of a whole remaining campaign. Illustratively, σ_d ≈ 0.01, δ_dec ≈ 0.001 and flips at every fork need ≈ 600 forks for 80 % power. The 300 in RB:227 is not derived, and the number of root instances (the clusters) is never stated.
- N0 is not a null if W binds: Prop. 10(a′) excludes hard budgets (T4rev:183).

*Fix.*
- Add the split-repetition bound U_split to route B: choose each fork's action from repetition 1, evaluate on repetition 2, swap. It is unbiased under the null; require UB₉₅(U_split) < δ_dec too.
- Size the forks from S0.5 for U_split, and pre-declare ≥ 30 instances.
- Use 5-fold cross-fitting and a cluster bootstrap that refits Ĉ in every replicate.
- Run N0 with a non-binding W.

## 4. MAJOR

**MA-1. The hard budget probably does not bind.**
At cap 40 with 51–66 % duplicates (DUPLICATE_RATE_PILOT_20261022:28–30) a campaign has ≈ 14–20 non-rule proposals, and KG verify does not fire (`control.py`:21–23). Executions stay below W = 20, skip and ghost then behave identically throughout, Δ_B ≡ 0, and element (2) is vacuous.

*Fix.* S0.5 reports P(W binds) per node. Pre-declare a W that binds in a stated share of campaigns (e.g. W = 10), or drop the budget claims.

**MA-2. The channel contrasts do not isolate the named conditions.**
- Under A2, Δ_I = C_ctrl − C_ghost is the seen-set alone (NF-c), not NI. *Fix:* give the seen-set its own arm, or relabel Δ_I as NF-c.
- The per-trial-seed check cannot remove an NF-c effect, because the filter works on configurations, not seeds. *Fix:* cut it, or retarget it at the BL-1(a) controller.
- Δ_F includes the keep. After a keep, later audited increments start from a different incumbent, so Δ_F mixes NF-a with NF-b and the shared incumbent error (T4rev:171–175). *Fix:* label Δ_F "manager feedback ∪ incumbent change" and read it with S1.1.

**MA-3. The controls skip the parts most likely to break.**
The scripted manager is deterministic: it consumes no LLM call (h `campaign.py`:1405–1408), sends no prompt and needs no seed determinism. P1, P2 and N0 can pass while ghost or controller-only leak a metric or seen-set entry on real nodes. Both arms need new code in `_complete_captured_trial` (h `snapshot.py`:788–866), whose captured hashes enter the novelty set (h `snapshot.py`:976–982).

*Fix.*
- Add fixture tests:
  - skip, ghost and controller-only give byte-identical manager prompts until the first controller difference;
  - the ghost record carries no metric or delta that the summariser reads;
  - the ghost configuration enters neither the controller's seen-set nor the novelty seen-set.
- Add one real-node positive control, e.g. digits at a W where Δ_B > 0 is expected.
- Power-match P1 and P2 to the real nodes' σ_d and fork count.

**MA-4. The schedule is off by 3–5×.**
Measured llama.cpp latency is 7.26 s per call (LLAMACPP_PROBE_DT_20261025:16), not the 1–2 s RB:227 implies, and a uniformly placed fork leaves ≈ 20 calls, not 15: 300 × 4 × 2 × 20 ≈ 48k calls ≈ 97 h per node serially, ≈ 12 days for three nodes.

*Fix.* Drop breast_w from S3; run ghost/controller-only on a pre-declared random third of E1 forks; use two serial servers if S0.1 passes on each; re-derive fork counts after BL-3.

**MA-5. The margin is inflated by trial-1 recovery, and its units are open.**
E[Y_myopic − Y_start] includes recovery from degraded starts (digits max Δ +0.217, LIVENESS_LLAMACPP_20261026:76; RB B5), which forks exclude. δ_Y can reach ≈ 0.02 ≈ 3 σ_node on the MLP nodes, a lenient non-inferiority margin, while the 0.002 floor is in metric units and Y is normalised.

*Fix.* Base δ_Y on E[Y_myopic − Y_after trial 1], or on σ_node (e.g. 0.5 σ_node). Declare it in raw metric units before S0.5.

**MA-6. Route A would not yet convince a DAC reviewer.**
Route A rests on an offline one-step improvement over a constant-prior rule on two CPU nodes; a DAC reviewer expects a learned state-dependent policy, deployed on held-out instances, beating the best static configuration. RB:193 leaves the online π′ run optional with no declared outcome.

*Fix.* Pre-declare online π′ vs best-static-g as the route-A confirmation, with its own rule. Keep S3c secondary; a label-table simulator assumes NF + NI and cannot represent feedback.

## 5. MINOR

- **mi-1.** U = E[max(Q_exec, Q_skip)] − E[Q_m] is biased upward by about σ_d/√π per fork, which is far above δ_dec, so "U < δ_dec" (RB:112) will not occur. Replace it with U_split (BL-3) or cut it.
- **mi-2.** Route A should use the Holm-adjusted bound (97.5 % for the first node). State that route B is an intersection–union test and needs no adjustment.
- **mi-3.** Reword "inconclusive" (RB:107) as: "neither a gain ≥ δ_dec nor its absence was shown; gains up to UB₉₅ remain compatible with the data".
- **mi-4.** State whether I_seq pools E1 and E2 forks, whether Ĉ is fitted per epoch, and how k_n counts the two.
- **mi-5.** Declare that `"vary"` departs from the MLP nodes' `fixed` policy (NOISE_FLOOR_COMMON_20261022:105–106); correct the fact-table items in §2.
- **mi-6.** P1's "theoretical gain ≥ 3 δ_dec" (RB:126) comes from the two-trial priced game. Set the control parameters by simulating the primary in the Track S regime.

## 6. What can be cut without weakening the decision

**Cut:** S2a (moot if W does not bind; Δ_B covers it); U as defined; the per-trial-seed check; breast_w in S3 (keep it in S1.1); S5 (it concerns a forecaster Track S does not run); ghost/controller-only on every fork.

**Keep:** S0.1, S1.1, S4a (≈ 1,000 calls ≈ 2 h), P2, N0, the E2 keep/discard forks.

## 7. What blocks acceptance

1. **BL-1:** declare the base controller. Either make P1 passable, or remove P1 and NI from route B.
2. **BL-2:** a single-unit π′ with no double-counted g, and a continuation-only primary against the best static g.
3. **BL-3:** the U_split guard on route B, derived fork and instance counts, and N0 with a non-binding W.

Settle MA-1 and MA-4 in the same revision; they decide whether element (2) and the 22 Nov date survive.
