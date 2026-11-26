# Paper C (working name) — when does autoresearch reduce to a contextual bandit?

> **Draft for author review, 26 Nov 2026.** The proposed research framing is for review before runbook drafting. The dated decisions in `docs/r1/PLAN.md` §10 govern execution.
> The R1-PAPERC rows are on `paperc-esyn-scaling-20261122`. Consolidation and an author decision on
> `R1-PAPERC-CORE` precede adoption of the revised primary contrast. The selected E-INT census is recorded
> below and in the [next-phase runbook](../docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md).

**Current status, 26 Nov 2026.** Implementation is on `paperc-esyn-scaling-20261122` under `paperC/`.
`codex/paperc-theory-20261117` and `mac-paperc-rl-20261121` have work outside that line. The existing consolidation
task remains queued. Paper C is outside Paper B's critical path.

## 1. Research question

When can a governed AutoML research loop be controlled with contextual one-step decisions under a hard worker-run
budget and manager-call cap, and when does modeling how actions change future search give a practically meaningful
gain? The proposer and controller are separate. The controller screens a proposal before spending a run (E1) and,
after observing its result, chooses whether to keep the candidate (E2). Verification and incumbent re-audits use
the declared action set and are charged to the same budget.

Paper B provides the exact fixed-price reduction under no feedback and no information, and tests one-step
controllers in live campaigns. Paper C tests the boundary of that reduction. Supervised fine-tuning or
distillation from a stronger teacher implements a decision model. The scientific comparison holds the available
information and immediate-value estimates fixed while changing which consequences the controller models.

## 2. Comparisons and claims proposed for the core

| Question | Comparison and evidence |
|---|---|
| Q1 — Does the longer horizon matter? | **Proposed primary contrast.** The strongest eligible frozen sequential controller versus a strong budget-aware one-step controller, selected on development campaigns and tested on fresh, paired campaigns. Retain the tuned static rule as a reference. |
| Q2 — When is a one-step controller sufficient? | Test a prediction about where the sign or size of an action's value changes. Vary the budget and the information or transition channel in synthetic worlds with an exact or certified oracle. Estimate the corresponding diagnostics before looking at real-task test campaigns. |
| Q3 — Is RL useful within sequential control? | Compare the best eligible RL method with the strongest eligible non-RL sequential method at matched information, interaction data and budgets. Keep the existing go/no-go for training RL. |
| Q4 — What does a small decision model add? | With the decision target and evaluation fixed, compare the tabular or rule implementation with a small model. Direct supervision and distillation are implementation variants. The on-policy distillation question stays open under P10. |
| Q5 — Which mechanisms explain the difference? | Measure budget allocation, information revealed by execution, proposer feedback, edit dependence on the incumbent and shared incumbent error. Isolate channels in controls and describe their measured contribution in real tasks. |

**Outcome.** Compare fresh-seed audited terminal improvement over the start under the same worker-run and
manager-call caps. Use the campaign instance as the paired unit and charge every evaluation available to the
controller, including verification or re-audit. Report the paired effect and its interval against the adopted
practical margin `delta_n`. Preserve the existing superiority and equivalence procedures where applicable.
An imprecise comparison is inconclusive. State equivalence for the locked comparators and tested regimes.
The existing E-T0 margin is `delta_n = max(0.002, 0.25 * s_tilde_n)` on the paired raw terminal gain,
using Paper B’s frozen paired noise scale `s_tilde_n`. The approved core row and the pre-declaration will bind
the exact contrast family, power and analysis.

## 3. Theory and the experimental test

1. **Exact reduction at a fixed price.** Reuse Paper B's one-step keep/execute rule and NF/NI as sufficient
   conditions. A positive synthetic control should reproduce the reduction.
2. **Budget pressure with exogenous proposals.** Build a reference controller that values the immediate proposal
   and prices the next run using remaining worker runs, proposal opportunities and an exogenous reference
   process. In the specified exogenous model, use finite-budget DP for the price. This isolates gains from
   budgeting alone. Keep the forecaster, legal actions and available observations matched in the key comparisons.
3. **Action-dependent continuation.** Derive a condition under which the difference in continuation value can
   exceed the immediate decision margin after accounting for budget. Seek a measurable bound or a testable
   prediction expressed through a channel such as edit interaction, policy-induced proposal changes or the
   informational value of a run. A continuation-value identity and existence examples establish the setup.
   The theory deliverable is a quantitative prediction that can be checked against controls or data.

Use E-SYN for isolated channels and oracle checks. Use the recorded `gemma4_31b` proposer with thinking off
for matched real-policy comparisons. Begin real measurement with the already recorded
`R1-PAPERC-MEASURE-FIRST` CPU work. `digits_mlp` and `tabular_mlp` are provisional E-T0 nodes. Prioritize E2
keep/discard and verification where the relevance checks find enough decision stakes. Include E1 only where its
screen can change decisions under the declared price and the existing relevance criteria are met. Track S stopped
before evidence collection. Its two controllers took the same actions in the pilot, which motivates checking
relevance before scaling.

The author selected **fixed-memory, variable-length sequence training** for the E-INT development census on
26 Nov. Test whether a batching edit makes a longer-context follow-up feasible or more valuable under a fixed
VRAM cap. The [next-phase runbook](../docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md#5-fixed-memory-variable-length-sequence-census)
specifies the four-cell comparison, fixed loss-bearing token count, independent evaluation, and reporting.
Keep E-INT descriptive. The workload, host, launch limits and seed block are fixed in its execution note.

## 4. Data and training

- **Reuse Paper B for immediate outcomes.** The two audited T0 sweeps support immediate forecasts, audit-based
  one-step references and development diagnostics. D.3's value-skip counts, proposal diversity and budget curves
  are useful for choosing which mechanisms to investigate. Reuse any labels within the declared split and
  authorization, with source and purpose recorded.
- **Collect action and continuation outcomes for the core contrast.** Default sweep logs follow the default
  actions and only observe their realized continuation. Keep the planned behavior mixture and repeated forks,
  using the recorded support and restore-fidelity checks. Live randomized action assignment with a fixed
  continuation is another design option for review if restore fidelity or cost makes it preferable. Separate
  E1 execute/skip observations from E2 keep/discard observations and use an independent terminal audit.
- **Train in stages.** First lock the immediate predictor and simple one-step, budget-only and non-RL
  sequential references. Then fit a small decision model or a teacher-based variant to the declared target.
  Evaluate frozen policies on fresh paired campaigns. Use the Paper C seed registry to exclude Paper B D.3
  instances and seeds from the Paper C test. A future-value label must specify the action, downstream policy,
  remaining budgets and audit outcome.

## 5. Current evidence and next decision

| Item | State |
|---|---|
| Paper C implementation | P0–P9 reviewed on the separate branch with 234 tests. E-SYN exact DP, certified oracle, policies, learners, fork and OPE checks are available. |
| Paper C evidence | Engineering runs only. There is no real-node run. Track S pilot findings are for feasibility and design, as recorded in its stop decision. |
| Paper B evidence to reuse | T0 proposal-level train/dev labels released. T1 formal labels and D.3 outcomes are pending in the current snapshot. |

1. Consolidate the Paper C branches on current `main` with PLAN decisions as additions only.
2. Complete the two CPU measurements in `R1-PAPERC-MEASURE-FIRST` through their runbooks and reviews.
3. Draft `R1-PAPERC-CORE` from the census. It should bind the primary comparator, qualified nodes and action
   epochs, finite-budget reference, one practical effect margin per node, and the boundary of the optional
   GPU evidence. Retain the existing rows on evidence access, support, equivalence and the RL go/no-go.
4. Use the adopted core row to write the evidence runbooks. Each runbook should state its claim, data source,
   eligible actions, budget and pairing, outcome and audit seeds, and what it can conclude at its measured
   precision.
