# Review of TRACK_S_SEQUENTIALITY_RUNBOOK_20261029 (independent, 29 Oct 2026)

AI-assisted review (Claude, fresh agent). Read-only check against `snap/apb` and `snap/harness`. This review does not edit the runbook and authorizes nothing.

## Spot-checks of §1 (8 claims)

| Claim | Verdict |
|---|---|
| D1 hard budget | **Confirmed.** PLAN:118–121; `c3_budgets` (`control.py`:351–363) makes both W and the LLM cap bind. |
| H1′ incumbent in prompt | **Confirmed** (`langgraph_manager.py`:122–141). The prompt also prints "Budget index (trial number)", so the manager knows the elapsed trial count. H5 is true only for the *remaining* budget. |
| H3 duplicates | **Confirmed.** `features.py`: `duplicate = cand_act in seen_metric`, and `observe()` returns before updating `seen_metric` on skipped rows. |
| B2 σ_node, 727/841 | **Confirmed** (NOISE_FLOOR_COMMON:105–113; DUPLICATE_RATE_PILOT:33). The D18 column shows **δ_n = 0.0020 on both primary nodes.** |
| D5 withdrawal | **Confirmed** (DI_TEST_MEMORY_ON_PARTIAL:127–133). |
| D1″ c = 1 | **Incomplete.** The LLM call is debited per proposal (`campaign.py`:1405–1408). But verify spends 2r worker runs (`campaign.py`:718–740), so W can bind before the LLM cap even at c = 1. See M1. |
| T4 rev. R1/R2 | **Confirmed.** Under the shared-incumbent-error model the loop lies "entirely outside" Prop. 10(a′), and hard budgets are not covered. |

## BLOCKING

**B1. G_D signs cancel, so its mean is blind to the channels it targets.** Take the information or budget value of executing. At band points where myopic executes, the forced skip loses that continuation value: the gain is −C. Where myopic skips, the forced execute gains +C. A band |index| ≤ b that is roughly symmetric averages to ≈ 0 even when C is large. The E2 keep/discard flips have the same problem.
*Fix.* Estimate the **signed action contrast** instead: continuation(execute) − continuation(skip), and continuation(keep) − continuation(discard). Here continuation = Q − audited immediate part, and each direction gets its own estimate. The primary is the continuation part, not total Q. The total also absorbs plain one-step miscalibration of V*/m_n or g, which is not sequential.

**B2. "Mean gain at near-threshold points" is the wrong policy-improvement statistic.** The one-shot-deviation argument is stated correctly for the positive direction. But what it bounds is the improvement of π′ = "deviate where A(s) > 0", which is E[A(s)⁺]-like and heterogeneous, not E[A]. The band also misses Prop. 10(c)-type gains, which sit far below threshold (V* ≪ g).
*Fix.* Pre-declare a few state features: budget fraction, trial index, key-seen, number of prior skips. Fit Â(s) on half of the fork points and evaluate E[A·1{Â > 0}] on the other half, so the max-over-noise bias cancels. Run the resulting π′ online as the route-A confirmation. The uniform-sample forks should count in the primary, not only the band.

**B3. The decision rule is incoherent and asymmetric, with a default that leaks.**
- (a) Under c = 2 the budget binds, so G_D,E1 > 0 is expected *from budget alone*. Route A can then fire on G_D while the "G_B only → budget-only" clause says the opposite.
- (b) Route A needs 1 of about 10 tests (G_D has two parts; Holm runs over 5 estimands × 2 nodes, and W and c are not fixed). Route B needs all 8 equivalences jointly. At 80 % power each, joint power is about 0.17.
- (c) "Inconclusive → B's wording" turns the likely outcome into B *without* evidence. That is the main post-hoc hole.
- (d) A route-A signal on the control node triggers an "investigation" with no declared outcome. B has no symmetric check.
*Fix.*
- Use **one primary estimand per channel** (budget, information, feedback) at a single pre-declared W (= 20) and c (= 2).
- Use a one-sided rule on each channel's improvement I. **A** if LB(I) > 0 and point ≥ δ. **B** if UB₉₅(I) < δ for every channel (non-inferiority; a negative I also favours myopic). **Inconclusive** otherwise, worded "no sequential gain larger than UB detected".
- Pre-declare which control-node findings void an A result, and add a positive control (M3) so that B is symmetric.

## MAJOR

**M1. The c = 1 "negative control" is invalid, and a STOP depends on it.** At c = 1 a skip can raise Y for three reasons:
- verify runs make W bind;
- skipping avoids false keeps under a misspecified prior (audits use fresh seeds);
- a skip changes later proposals (NF-a, NF-c).
"Skipping cannot raise Y" holds only under NF + NI with a correct prior, which is the hypothesis being tested.
*Fix.* Drop c = 1. Replace it with synthetic controls that use the deterministic scripted manager (no LLM): an NF + NI node with fresh per-run seeds and additive increments, where every G should be 0.

**M2. The channels are not identified, because forced execution changes budget, information and display at once.** S4b isolates only skip display, and H1′ makes keep feedback impossible to ablate.
*Fix.* Add **ghost-run** arms at E1 forks:
- skip;
- ghost: run, debit, result hidden from controller, memory and seen-set;
- controller-only: as ghost, but the forecaster sees the result;
- full execute.
Successive differences give budget, then information (NI), then manager feedback (NF-a/c). Report the interactions. This is about 50 lines of override code and makes S3b ProbeFirst redundant.

**M3. There is no positive control, so a null result is uninterpretable.** A reviewer will ask whether the test can detect sequentiality at all.
*Fix.* Use a scripted-manager node built on Prop. 10(c) (probe, then a correlated larger edit) and one on Prop. 10(b) (keep shifts the proposal law). The pipeline must recover G > δ there before any route-B claim.

**M4. The margin and the power are mismatched.**
- δ_n = 0.002 is a quarter of a *single-comparison* noise sd, defined in metric units for a 20-run summed one-step gain (PLAN D18). Y is "normalised per node" (PLAN:118), so check the units. The margin is also undefined at W = 40.
- The paired sd of terminal-Y continuations after a fork is plausibly 0.005–0.015. TOST at δ = 0.002 then needs about 140–500 forks per estimand per node, not 60. With 18 instances, S2b–S4b give an SE ≈ σ_d/√18, roughly δ or larger, so route B is out of reach there.
*Fix.*
- Express δ in Y units, either as δ = max(0.002, 0.1 × E[Y_myopic − Y_start]) per node or as an explicit relative margin, which DAC readers expect.
- Size the S0.5 pilot on the sd of **different-LLM-seed same-action** pairs. Same-seed pairs are identical under frozen worker noise and deterministic decoding, so their null sd is ≈ 0.
- Power for the joint B rule.
- Declare common random numbers: deviation and myopic branches share LLM and worker seeds.

**M5. Route B cannot be called "provable."** NF-c fails by construction (H3). NF-a/keep feedback is always present (H1′). R1 places the shared-error model outside 10(a′), and R2 excludes hard budgets.
*Fix.* Word B as "empirically approximately one-step (≤ δ) despite known violations of NF/NI". Add an arm that varies worker seeds per trial, to tell whether any information effect is a frozen-noise artefact (R1, last paragraph).

**M6. The multisecretary recursion does not match the loop.**
- Verify costs 2r extra runs, so weights are random (a dynamic knapsack).
- Revisions and duplicates consume LLM calls.
- Rewards are not additive, because Y is the final incumbent and gains compose through the incumbent.
- V*_n is non-stationary.
- The cited source is uncertain.
*Fix.* State the DP as an NF + NI approximation over (proposals left, runs left) with verify weights. Cite the stochastic knapsack literature and Arlotto & Gurvich (2019, bounded regret for the multisecretary problem). Keep G_B **offline only** (S2a). It is an OR fact, not DAC evidence; run S2b only if S2a ≥ δ.

**M7. Missing DAC evidence for route A.** A positive one-step deviation shows that myopic is improvable. The DAC headline still needs a *learned* policy with multi-step credit, for example fitted-Q or PPO on a simulator calibrated from label tables, compared with the contextual-bandit arm at matched data.
*Fix.* Add this as a secondary. For route B, add a **hindsight upper bound**, the best decision sequence over the fork tree. If even that is < δ, B is strong.

## MINOR

- **S0.1.** 95 % per-call identity gives about 0.95²⁰ ≈ 36 % identical campaigns. State whether the check is per call or per campaign. Forks resume from snapshots, so the prefix needs no LLM replay. Replace "prefix replays" with an A/A check: rebuild the controller at the fork, take no deviation, and require decisions identical to the root.
- **Controller rebuild (H4).** Include the A/A check above in the S0.3 tests.
- **Trial 1.** Paired differences cancel trial-1 recovery. Changing the start configuration departs from the sweep-1 and deployment nodes, so declare it, or keep the deployed start and simply exclude trial 1.
- **Manager swap.** The optional stronger manager depends on S4a results. Make it secondary-only.
- **S0.2(c).** Track S must use the deployment's duplicate-horizon rule.

## What to drop to decide by ~22 Nov

Drop:
- c = 1;
- W = 40, or make it the single primary;
- S2b;
- S3b ProbeFirst and KG, now covered by the ghost arms;
- the GPU extension.

Keep, all cheap:
- S1.1, S0.1, S4a and S5;
- S2a (offline);
- the redesigned S3a on `digits_mlp` and `tabular_mlp`, with `breast_w` as control;
- the synthetic positive and negative controls.

Feasibility: about 300 forks × 4 arms × r = 2 × ~15 calls ≈ 36k serial LLM calls per node, about 10–20 h. That fits after sweep 1 if the S0.3 code and review land by ~5 Nov. The current full matrix does not fit.
