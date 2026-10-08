# Paper B controller design v2 — two-checkpoint verification timing

2026-09-27, revised after review comments. This document **supersedes** the
controller definitions in B1/B4 (manuscript `05_method.tex`,
`control/controllers.py`) and the "frozen reserve/VOI = primary comparator"
reading of `B_DECISIONS_20260927.md`. Everything else in RUNBOOK §12 stands.
Nothing here is evidence. All results are PLANNED.

> **2026-09-29 note (review M-2):** the BAVAR / Strategic Verification
> citation (preprints.org 202608.2057) is **not verified at source**: the
> site blocks automated access, including through the author's Chrome
> (2026-09-27, 2026-09-29). Read "§4.2" in §4 and "verified 2026-09-27" in §8
> as unverified until an author checks the preprint. The manuscript no longer
> attributes a section, and the implemented scheduler's signals and
> deviations are listed in `control/timing.py` and `05_method.tex`.

**Approval wording (author):** Proceed with the revised fix queue and CPU
validation. Adopt the two-checkpoint option-value direction, but first correct
the continuation targets, the template-family cross-fitting, the hard-budget
allocator and the comparator definitions. Keep replay sensitivity in evaluation,
with explicitly scoped assumptions. Remove unsupported optimality, novelty and
null-result claims. Live execution remains subject to the existing
qualification and bounded-run gates.

---

## 1. Decision problem and information

- Each original root offers at most **one** verification. There are two online
  decision points: checkpoint 1 with history **H₁**, and checkpoint 2 with
  history **H₂**. H₂ **includes H₁**. If a feature map drops H₁, the sufficiency
  assumption must be stated explicitly.
- Across an evaluation batch of N original roots, the **hard budget** is
  B = floor(0.25·N) verifier calls in total. This is a different constraint from
  "one per root", and both hold.
- Deployment protocol (a modelling assumption, declared in the contract): the
  batch is **phase-synchronous**. All checkpoint-1 decisions are made before any
  checkpoint-2 information exists. Checkpoint-2 decisions are made in a second
  phase over roots that reached checkpoint 2. Asynchronous streaming is out of scope.
- Outcome U ∈ [0,1] (primary; RUNBOOK §12.2). Verifier costs remain separate
  budget constraints and are not folded into U.

## 2. Data: the paired tree (unchanged principle, sharper wording)

For each root:
- **now** leaf: verify at checkpoint 1;
- a continue branch run to checkpoint 2. If checkpoint 2 is reached, the
  **later** leaf (verify) and the **never** leaf (continue) **fork from the same
  checkpoint-2 state**. If it is not reached, later ≡ never by fallback;
- ≥2 stochastic repetitions per leaf where the budget allows (design:
  2 roots × 2 repetitions per family).

Leaf outcomes are **noisy samples**. The tree supports *paired* estimation. It
does not reveal each state's conditional advantage exactly. Conditional
expectations are learned by regression across roots. Required lineage checks:
- same checkpoint-2 state for later and never;
- no transplanted states;
- no information from after the decision time in any decision input;
- all descendants and repetitions stay in their root's template family and split.

Other experimental designs can also learn and evaluate timing policies. Paired
trees offer one particular measurement advantage (paired counterfactual
contrasts on identical roots), not exclusivity.

## 3. The proposed controller: fitted continuation-value timing rule

This is standard optimal-stopping methodology: least-squares continuation-value
estimation (Longstaff & Schwartz, 2001) and two-step fitted Q-evaluation,
**applied** to agent verification timing. It is not claimed as a new method.

**Folds.** K folds split by **template family**. Each fold keeps all of the
family's roots, descendants and repetitions together. Every quantity used for
root i comes from models fitted without i's family.

1. **Second-stage policy.** On other folds, regress the paired contrast
   (U^later − U^never) on H₂ over reached roots, giving Â₂^(−k). The
   implementable decision is d̂₂^(−k)(H₂) = 1{Â₂^(−k)(H₂) > c₂}, where c₂ is
   calibrated on development folds.
2. **Continuation target (corrects the max-bias).** Do not use max(Â₂, 0);
   an independent noisy estimate still has an upward-biased positive part.
   Instead, use the **out-of-fold decision times the observed paired outcome**:

   Y_wait,i = reached₂,i · d̂₂^(−k)(H₂,i) · (U_i^later − U_i^never).

   Regress Y_wait on H₁ to get **V̂_wait(H₁)**: the continuation value of the
   *fitted second-stage policy*. This is an implementable policy's value, not the
   oracle option value.
3. **Immediate value.** Regress (U^now − U^never) on H₁ to get **Â₁(H₁)**.
4. **Checkpoint-1 score:** s₁^prop(H₁) = Â₁(H₁) − V̂_wait(H₁), the net value of
   using the check now rather than keeping it.
5. Under the shared budget (§5) this is a **budget-constrained heuristic**. It is
   **not** the optimal policy for the batch-constrained problem, and must not be
   called optimal.

## 4. Comparators and ablations (matched information and tuning)

Every controller gets the same inputs (H₁ at checkpoint 1, H₂ at checkpoint 2,
remaining budget and progress), the same model family and capacity, the same
template-family folds and the same **tuning budget** (the same number of
candidate configurations and the same development data). Each controller calibrates
its **own** cutoffs and reservation parameter under that budget. Identical
numeric cutoffs across controllers are not required, because they are not fair.

| Role | Controller | Checkpoint-1 score | Checkpoint 2 |
|---|---|---|---|
| **Primary** | Repeated-myopic | Â₁(H₁); verify if > c₁ | Â₂(H₂) > c₂ |
| **Primary** | **Context-dependent VOI scheduler (BAVAR-inspired)** | Learned scorer over BAVAR-style signals: actor uncertainty (e.g. candidate disagreement), action criticality, verifier reliability estimated on development data, expected information value (a predicted immediate verification gain), progress (checkpoint index, remaining horizon) and remaining budget. Hard reserve fraction tuned on development data | the same scorer at H₂; verify only if > c₂ |
| Ablation | Constant reserve | Â₁(H₁) > τ, τ a constant fixed on development data | **Â₂(H₂) > c₂** (fixes the current bug: never verify at checkpoint 2 when the predicted advantage is negative) |
| Diagnostic | Fixed now / later / never | — | — |

The BAVAR-inspired scheduler is an **adaptation**, not a reproduction. Its
docstring and the manuscript list every deviation from BAVAR §4.2 (signals
available in this task, no multi-verifier choice, no RL training loop).
Beating the constant-reserve ablation says nothing about BAVAR; only the
context-dependent scheduler is a primary comparison.

## 5. The shared, executable budget allocator (used by every controller)

The same allocator applies to all controllers. Controllers differ only in their
scores s₁ and s₂, their cutoffs c₁ and c₂, and their reservation R.

1. **Inputs:** batch roots with feasibility masks; B = floor(0.25·N);
   controller parameters (c₁, c₂, R ∈ [0,B]).
2. **Phase 1 (checkpoint 1).** Rank the feasible roots by s₁, descending. Ties
   are broken by a declared outcome-blind hash of the root ID. Verify the top
   roots with s₁ > c₁, up to k₁ = min(#eligible, B − R). Infeasible roots take the
   continue fallback.
3. **Phase 2 (checkpoint 2).** Remaining capacity is B − k₁. Eligible roots have
   reached checkpoint 2, are unverified and feasible. Rank by s₂ (same tie rule)
   and verify the top roots with s₂ > c₂ until capacity is exhausted. Roots that
   terminated early never enter phase 2.
4. **Unspent capacity** stays unspent. Record realized calls, unspent calls and
   total work per controller.
5. **Tests** cover: exhaustion in phase 1; reservation larger than phase-2 demand;
   ties; all infeasible; no root reaching checkpoint 2; B=0; and that no root is
   verified twice.

## 6. Evaluation (held-out template families)

- Policies and cutoffs are **frozen** before test data. Each decision sees
  only decision-time information. All controllers share the recorded continuation
  and verifier regimes.
- For each held-out batch, **re-run the allocator** with frozen scores. Each
  root's realized regime selects its leaf (now / later / never, averaged over
  repetitions). Policy value is the mean U over **all** original roots.
- Uncertainty uses a template-family cluster bootstrap with shared draws across
  controllers. The allocator is **re-run inside every draw** so that batch
  coupling is reproduced.
- **Primary contrasts:** proposed − myopic and proposed − BAVAR-inspired, with
  simultaneous intervals (Bonferroni over 2).
- **Pre-registered reading of each contrast** (practical margin .02 U):
  - *supported:* the adjusted LCB > 0;
  - *practically large:* the adjusted LCB > .02;
  - *equivalence evidence:* the adjusted interval lies within (−.02, .02);
  - *falsified as practically useful:* the adjusted UCB < .02 **and** the precision
    target was met;
  - *inconclusive:* anything else. No budget expansion follows.

## 7. Replay sensitivity (N1) sits in evaluation only

- Controllers never use p. N1 **qualifies conclusions**. It does not produce a
  measurement-aware controller or a deployment safety guarantee, and the
  manuscript must say so.
- **Event.** D_path(i) = an outcome-relevant discrepancy anywhere in root i's
  recorded H₁, H₂ or the leaf outcomes used by *any* compared controller.
  p_path bounds P(D_path). Checkpoint bounds combine by min(1, p₁+p₂) only when
  each is valid.
- **Interference.** Under shared batch allocation, a wrong score at root j can
  change root i's allocation. The per-root 2p argument does not cover this.
  Required: derive the displacement constant m for the §5 allocator, i.e. the
  maximum number of roots whose realized regime can change when one root's
  recorded information changes. Candidate: m ≤ 3 (the root itself, one displaced
  in phase 1, one displaced in phase 2 through the capacity shift). This must be
  proved and tested by planted single-root perturbations. The population-contrast
  tax is then ≤ 2·m·p_path.
  - Until the derivation is reviewed, the p-grid report states that it covers
    per-root effects only, not allocation interference.
- **Report:** for each primary contrast, the largest p in {0, .005, .01, .02,
  .05, .10} at which the adjusted conclusion survives, with its assumptions stated.

## 8. Claims discipline

- **Contribution:** the agent setting, the paired counterfactual measurement design,
  and convincing evidence on it, with explicitly scoped replay sensitivity.
  **Not claimed:** a new timing method, optimality, a safety guarantee, or
  exclusivity of branch trees.
- **Nulls are not explanations.** Similar controller performance does not show that
  waiting value is constant. Similarity to myopic does not show that checkpoint 2
  is uninformative. A null result is not automatically publishable.
  Before interpreting any null, report:
  - achieved precision against the .02 target;
  - out-of-fold quality of Â₁, Â₂ and V̂_wait (calibration and ranking);
  - estimated heterogeneity of V̂_wait across roots, with its uncertainty;
  - the ranking quality of Â₂ at checkpoint 2.
- **Required citations:** BAVAR (Adeli, preprints.org 202608.2057, verified 2026-09-27),
  Calibrate-Then-Act (Ding, Tomlin & Durrett, arXiv 2602.16699, verified
  2026-09-27), Calibration Is Not Control, Longstaff & Schwartz (2001) for
  continuation-value regression, and fitted-Q evaluation.

## 9. Answers to the three confirmations

1. Proposed = fitted continuation-value rule: **yes**, with the §3 targets and the §5 budget handling.
2. Reserve/VOI: **a constant reserve is only an ablation**. The primary comparator
   is the context-dependent BAVAR-inspired scheduler.
3. Later and never from the same checkpoint-2 state: **yes**, with lineage checks,
   stochastic repetitions and no leakage of information from after the decision.
