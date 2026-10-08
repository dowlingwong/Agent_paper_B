> Copied from the source repository at S = 4154f153, 7 October 2026; this file keeps the B part of SCOPE.md.
> The source copy in agent-checkpoint-intervention is the historical one.

# Scope decision — Paper B

Updated September 26, 2026. [RUNBOOK.md](RUNBOOK.md) version 2 is the governing
plan; this repository's [STATUS.md](STATUS.md) is the progress log. This scope
decision promotes no result.

Paper B asks: what should a controller estimate and do under intervention
budgets and harm constraints? Its core is a learned one-step continue/verify
control with strong matched baselines. Its extension is two online decision
opportunities under a shared within-trajectory budget: act now or preserve
verification for later. The evidence floor is new qualified agent data, frozen
policies and a held-out comparison; the sequential lane is separately qualified.
A defined recovery is optional; broader horizons and DAC/RL beyond the bounded
extension are deferred. Publication is one combined paper if the sequential gate
supports it, otherwise a disclosed coherent core-only route.

There is no separate Paper C implementation deliverable. Its temporal question is
incorporated into B's staged development; sequential findings remain PLANNED.
One-step evidence cannot establish sequential value or safety automatically.

B's controller is the scientific deliverable. Measurement contracts support it.
Live qualification/pilot/main work requires its own bound runtime, resources and
authorization.

The prior E0–E5 registrations, sample counts, success windows, signatures and
outcomes stay historical and are not inherited by b_v2. The active contract is
`protocols/paper_b/contract_v3.yaml`; `contract_v2.yaml` and `contract_v1.yaml`
remain historical and active consumers reject v1. Engineering and qualification
are the only implemented phases; later phases refuse. No v1 data are silently
recoded.

Qualification precedes causal interpretation; pilot, training, validation,
calibration and test templates are disjoint; all descendants remain within their
original split/cluster. No positive pilot p-value or desired risk/advantage
anticorrelation is required. Existing evidence and negative findings are retained.

COMBINE versus CORE_ONLY is decided on validity, precision, resources and a
coherent temporal question before confirmatory outcomes. If both studies run,
both are reported, including null or unfavorable results. Neither route predicts
venue acceptance.

Prior-disclosure details remain in [PRIOR_DISCLOSURE.md](PRIOR_DISCLOSURE.md) and
require a fresh author assessment of the method-level comparison in §7. The
supplied ETAAI PDF has been read and cited; its overlap verdict remains open. The
former scope record is preserved in the source repository's planning archive.

## Amendments of September 26 (RUNBOOK v2.1 §11)

These change order and emphasis. They do not change the evidence rules above.

- **B (author decision):** two proposed increments over the nearest prior.
  N1, measurement-aware pessimism, now a *validity constraint*: a fixed policy's
  population lower bound is reduced by 2p under a declared joint discrepancy
  event. There is no pointwise gate from a global p (RUNBOOK §12.2). N2, the
  option value of verification: one three-leaf tree per root (verify-now /
  continue→verify-at-2 / never), which replaces the recovery arm and serves both
  the one-step and the two-decision estimands. B's contribution statement is
  rewritten after the novelty memo.
- **Dated gates (historical planning targets):** B novelty memo Oct 3;
  interface-amendment screen Oct 17; B pilot report Nov 14; ICML go/no-go
  Nov 30; route decision Dec 7. The adopted internal cutoffs are 15 November
  (both lanes qualified) and 30 November (pilot done, route chosen, design
  frozen, budget authorized); see [OPEN_ITEMS.md](OPEN_ITEMS.md).

## Decisions of 27 September (RUNBOOK §12)

- **B:** verification timing (N2) is the central question, against
  repeated-myopic and reserve/VOI comparators. N1 is a population-scope validity
  constraint with p as a sensitivity assumption (grid 0–.10, working .02).
  Primary outcome U. New two-checkpoint candidate-consistency task on Devstral
  24B/Ada. Bounded screen + pilot cap of 512 leaves. ICML 2027 target.
