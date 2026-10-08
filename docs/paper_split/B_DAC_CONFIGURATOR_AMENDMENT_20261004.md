# Paper B amendment: dynamic algorithm configuration framing and the configurator

2026-10-04. **Status: PROPOSED design + CPU scaffold.** The author asked for this
amendment and the scaffold. The author has **not** yet adopted the decisions in
§6. Nothing here is evidence. This amendment does not change B's estimands,
primary outcome U, the controllers' definitions, the shared allocator, the
comparators, the budget, the N1 evaluation or the gate sequence (RUNBOOK §12,
§12.2a, B_CONTROLLER_DESIGN_20260927.md). It does **not** unblock B1
(task realism) or B2 (R2 re-review, novelty verdict); see §8 and
[B_READINESS_AUDIT_20261004.md](B_READINESS_AUDIT_20261004.md).

Amends RUNBOOK §14.2 "RL/DAC connection". That paragraph says general DAC is
"a separate extension, not completed contributions introduced by a new
citation". This amendment keeps that rule for *method* claims. It proposes DAC
only as the **framing vocabulary** for B's existing two-checkpoint problem,
plus one implementation choice: the decision histories may include frozen
text-encoder features.

---

## 1. Why DAC, and what it does not buy

Dynamic algorithm configuration (Biedenkapp et al., ECAI 2020; Adriaensen et
al., JAIR 2022) learns a policy that sets an algorithm's parameters *during* a
run, conditioned on instance features and the run's state. It is formalised as
a contextual MDP and evaluated on held-out instances. B already has this shape:
the target algorithm is the executor agent, and the configured parameter is
whether to spend the verification at each checkpoint.

The framing buys:

- **Vocabulary that venues recognise.** Context = instance family, state = run
  history, policy = configurator, generalisation tested on held-out instance
  families. That last item is exactly B's template-family split.
- **A home for the encoder choice.** In DAC terms, the encoder is part of the
  state representation.
- **Clean comparators.** Repeated-myopic is a greedy configurator. The constant
  reserve is a static configuration schedule. The VOI scheduler is a
  hand-structured dynamic configurator.

The framing does **not** buy:

- **A theorem or an optimality claim.** The proposed rule stays a
  "budget-constrained heuristic" (design v2 §3.5).
- **A Markov guarantee.** H₂ contains H₁, so full history is retained. Any
  compressed state needs the sufficiency declaration that already exists.
- **A new method.** Two-step fitted-Q (Longstaff–Schwartz) *is* the two-step
  solution. A DAC reviewer's natural question, "why not RL?", is answered by
  that equivalence and by the data scale (§3), not by novelty.

Two deviations from standard DAC must be stated in the manuscript:

1. **Budget-coupled instances.** Standard DAC learns per-instance policies.
   Here, one hard budget B = floor(q·N) couples a batch of roots through the
   shared two-phase allocator (design v2 §5). Call it *budget-constrained*
   DAC. The allocation-interference constant m ≤ 3 (N1_DISPLACEMENT.md) is a
   consequence of this coupling.
2. **Minimal horizon and action set.** There are two decision points and a
   binary action, with at most one verification per root. B is a minimal DAC
   instance with paired counterfactual leaves. It is not a DAC benchmark.

## 2. Mapping

| DAC element | Paper B object | Where it lives |
|---|---|---|
| Instance distribution | Template families of the B task | task generator; split manifest |
| Instance context | Task descriptor, visible at checkpoint 1 | H₁ |
| Target algorithm | Executor agent (Devstral-Small-2-24B on Ada) | runtime binding (contract) |
| Configuration space | {continue, verify} at checkpoints 1 and 2; ≤1 verify per root | `allocator.py` |
| State at step t | Decision history H_t (H₂ ⊇ H₁); partial observability acknowledged | `DecisionView`; serialiser |
| Reward | U ∈ [0,1], hidden-test accuracy of the final valid candidate | evaluator |
| Cross-instance constraint | B = floor(0.25·N) calls per batch | shared allocator |
| Configurator policy | score functions (s₁, s₂) + shared allocator + tuned (c₁, c₂, R) | `timing.py` |
| Generalisation test | held-out template families; family-cluster bootstrap | `evaluate_tree.py` |

## 3. The configurator, and why "fine-tuning" means fitting heads

The configurator has four parts, applied identically for every controller:

1. **Serialiser.** Turns H_t into a decision-time text view.
2. **Frozen encoder.** Turns text into vectors (a slot: Kev or CLM, §4.2).
3. **Outcome-blind projection.** Fitted on development roots only.
4. **Shared value heads.** These are the existing ridge models: A₁, V_wait and
   A₂, the VOI scorer, and the myopic and reserve scores, all with one `l2`.

Fitting the configurator means fitting parts 3–4 on development families. In
the primary design, **no encoder weights are updated.** Reasons:

- **Data scale.** The bounded screen plus pilot give at most 16 + 64 = 80
  original roots in 8 + 32 = 40 families (RUNBOOK §12.2). Five family folds
  leave about 64 training roots per fold, and the targets are noisy paired
  contrasts in [−1, 1]. Kev's own fine-tuning guide asks for a few hundred to a
  few thousand labelled examples; CLM's trainable heads have about 20M
  parameters. Either would memorise.
- **Matched information and capacity** (design v2 §4). Every controller must
  get the same inputs and model capacity. A frozen encoder gives all
  controllers identical features at no extra cost. Fine-tuning per target
  would turn the primary contrasts into comparisons of fine-tuning effort.
- **Targets are continuous.** Both encoders' native training objectives
  classify typed answers. The value heads need regression on paired outcome
  contrasts, which the existing ridge already does with family cross-fitting.

Encoder fine-tuning (Kev LoRA, CLM head retraining) is an **optional later
extension**. It needs separate authorisation and an independent labelled set
of at least several hundred decisions from families outside every evaluation
split. It is never fitted on test families or their descendants.

## 4. Components as scaffolded

Package: `experiment_scaffold/src/causal_branch/control/configurator/`. CPU
tests: `tests/control/test_configurator.py`. Scripted trees:
`experiments/paper_b/configurator_scripted.py`.

### 4.1 Serialiser (`serialiser.py`)

- **Allowlisted event kinds only.** task, assistant, tool_call, tool_result,
  observation, checkpoint. Any other kind (grade, outcome, hidden) is
  rejected, not filtered.
- **No post-decision information.** Events after the checkpoint step are
  rejected.
- **H₂ extends H₁ exactly.** H₁'s events must be a prefix of H₂'s; a
  transplanted checkpoint-2 history is rejected.
- **Redaction.** Root, template and family identifiers are replaced with
  `<id>`.
- **Deterministic truncation.** The task statement (capped) is always kept,
  then the most recent events, with an explicit omission marker. The default
  budget is 6,000 characters, conservative for CLM's 2,048-token reference
  context. Each serialised text gets a sha256, and the serialiser
  configuration gets a fingerprint.

### 4.2 Encoder slots (`encoder.py`)

| Slot | Representation | Host | State |
|---|---|---|---|
| `MockEncoder` | signed feature hashing (1–2-grams) | CPU | tests only; never a result |
| `KevEncoder` | calibrated answer probabilities to a **frozen typed-question set** (draft `KEV_QUESTIONS_DRAFT`: candidate staleness, shift suspicion, candidate quality, expected verification gain, progress) | Mac (MLX) or CUDA, offline from saved transcripts | **stub**: refuses without a complete `KevBinding` (revision, URL, backend) and `allow_network=True`; response parsing tested through a fake transport |
| `CLMEncoder` `clm_state_head` | Qwen3-8B last-token pooled embedding → frozen CLM state head (4096→512) | Ada (vLLM pooling server) | **stub**: refuses without a complete `CLMBinding` (backbone revision, URL, head path + sha256); request/projection code unexercised |
| `CLMEncoder` `backbone_raw` | Qwen3-8B embedding without the CLM head | Ada | ablation separating CLM post-training from the backbone |

Every vector is cached by (encoder fingerprint, text sha256). The fingerprint
covers the model revision, head hash, variant and question-set digest. It does
not cover the URL. A changed artifact therefore cannot reuse a stale vector.

**Kev versus CLM.**

- **Kev** is easier to run: offline on a Mac, low-dimensional, interpretable,
  with calibrated probabilities. Its training is general document
  classification, not agent trajectories. Its question set is a researcher
  choice that must be frozen before the pilot.
- **CLM** is post-trained on agent trajectories and is the nearest domain to
  "is this candidate worth checking?". It needs an exact pooling setup on Ada,
  and its default context is 2,048 tokens.

The choice is D-DAC2 (§6).

### 4.3 Projection and heads (`heads.py`)

- **`EmbeddingProjector`.** Mode `pca` centres, keeps the top-k principal
  directions and whitens; it is for CLM. Mode `standardize` keeps every
  dimension and centres and scales it; it is for Kev. The projector is fitted
  on **development roots only**, with H₁ and H₂ texts pooled, and it is
  outcome-blind. Within the development set it is fitted once across the
  development folds. That is transductive but uses no labels, which is
  declared here. Test texts never enter the fit; a CPU test confirms that
  perturbing every test text leaves the projector unchanged.
- **`FeatureMap`.** Writes `e1_##` into h1, and `e1_##` + `e2_##` into h2, so
  H₂ ⊇ H₁. Unreached roots get zero `e2_##`. They are never scored at
  checkpoint 2, so this only keeps the design matrix rectangular.
- **Feature sets** (the ablation axis): `telemetry` (current design),
  `embedding`, `telemetry+embedding`.
- **`evaluate_with_configurator`.** Fits the map on development roots,
  augments both sets and calls the **unchanged** `evaluate_tree`. It returns
  the report plus provenance: encoder fingerprint, serialiser fingerprint,
  projector digest, development-roots digest and feature keys.

## 5. Proposed contract fields (draft; not written into contract_v2.yaml)

```yaml
configurator:
  schema: b_dac_configurator_v1
  feature_set: null            # telemetry | embedding | telemetry+embedding (D-DAC4)
  encoder:
    slot: null                 # kev | clm_state_head | backbone_raw (D-DAC2)
    model: null                # e.g. jaredpalmer/kev-4b or Qwen/Qwen3-8B
    revision: null             # HF commit hash
    head_sha256: null          # CLM only
    question_set_sha256: null  # Kev only (D-DAC3)
    backend: null              # mlx | torch | vllm-pooling
  serialiser_fingerprint: null
  projection: {mode: null, k: null}   # D-DAC5
  fitted_on: development_families_only
  encoder_weights_updated: false
```

## 6. Author decisions required before any pilot outcome exists

| ID | Decision | Recommendation |
|---|---|---|
| D-DAC1 | Adopt DAC as B's framing vocabulary (amend RUNBOOK §14.2 as in this file), with the two declared deviations (§1) and no method claim | adopt |
| D-DAC2 | Primary encoder slot; the other becomes an ablation | Kev if ease of running and interpretability matter most; CLM if domain fit matters most. Either is defensible if chosen now. |
| D-DAC3 | Freeze the Kev question set (wording, levels, order), or the CLM variant | freeze before attempt 2 runs; the draft is a starting point |
| D-DAC4 | Primary feature set | `telemetry+embedding` primary, `telemetry` reported as an ablation |
| D-DAC5 | Projection `k` (PCA) or `standardize` (Kev) | `k = 8` for CLM; `standardize` for Kev |
| D-DAC6 | Model size for Kev (0.8B / 4B / 9B) | 4B: validated 8k context, runs on a 32 GB Mac |

Choosing any of these after seeing pilot outcomes would be a forking path, so
it is not allowed.

## 7. Work items this adds

- **B-DAC4 · history capture (W, prerequisite).** The tree driver and the live
  task do not record any agent transcript. `execute_tree_v2` exposes only
  workspace hashes. Add a per-branch `DecisionHistory` record (JSON via
  `history_to_json`) at each checkpoint, plus a lineage check that the later
  and never leaves share the checkpoint-2 history. Without this, no encoder
  has anything to read.
- **B-DAC5 · contract v3 fields (W, then D).** Add the §5 block when D-DAC1–6
  are decided.
- **B-DAC6 · matching report (W).** Add the configurator provenance to
  `matching_report` so it fails if controllers ever see different feature
  maps.
- **B-DAC7 · encoder binding (X/D).**
  - Kev: download a pinned revision and run offline on the Mac.
  - CLM: a Qwen3-8B pooling server on Ada, with backbone and head hashes
    recorded at qualification.

## 8. Relation to the open blockers

- **B1, task realism.** F9 failed: the typical behaviour has no now-best family
  and the verifier never beats refitting. Reproduced on 4 Oct. A configurator
  cannot fix that. If no family rewards verifying now, no representation has
  anything to rank. Attempt 2 (P-B1) is judged on its frozen realism criteria,
  **not** on configurator performance. Task mechanisms must not be chosen so
  that text features "win".
- **B2, R2 re-review, novelty verdict, BAVAR reading.** Unchanged by this
  amendment.
- **Cutoffs (P-B2).** 15 Nov and 30 Nov stand. B-DAC4–B-DAC7 must fit inside
  them or be dropped. The configurator is not a reason to move the cutoffs.

## 9. Validation (4 Oct 2026, CPU, Python 3.12 venv, requirements.lock)

- `tests/control/test_configurator.py`: 22 tests pass. They cover:
  - serialiser rejections, redaction, truncation and prefix lineage;
  - mock determinism;
  - Kev and CLM refusal without a binding, with no network call;
  - Kev response parsing;
  - fingerprint and cache keying;
  - projector development-only fitting;
  - H₂ ⊇ H₁ for every feature set;
  - outcome and identifier absence from texts;
  - end-to-end `evaluate_with_configurator` for all three feature sets and the
    Kev slot;
  - family-overlap refusal.
- `tests/control`: 188 tests pass, including the above. `tests/release`: 5
  pass.
- `tests/measurement`: 36 pass. A first run errored in one replay-panel test
  because the sandboxed shell could not delete a temp directory. The rerun,
  with deletion allowed, passes.
- The suite's supplement self-check printed 86 entries in the first run and 93
  in the rerun. 93 matches the 4 Oct VALIDATION record. The first run coincided
  with another session's Paper A work in the same tree; this is not
  investigated further here.

## References (verify at source before manuscript use)

- Biedenkapp, Bozkurt, Eimer, Hutter, Lindauer. *Dynamic Algorithm Configuration: Foundation of a New Meta-Algorithmic Framework.* ECAI 2020. doi:10.3233/FAIA200122.
- Adriaensen, Biedenkapp, Shala, Awad, Eimer, Lindauer, Hutter. *Automated Dynamic Algorithm Configuration.* JAIR 75, 2022. arXiv:2205.13881.
- Biedenkapp et al. *TempoRL: Learning When to Act.* ICML 2021 (already cited in RUNBOOK §14).
- Longstaff & Schwartz, 2001 (already cited in design v2).
- Kev: https://github.com/jaredpalmer/kev (Kev 1.0; Apache-2.0). CLM: https://github.com/Contrastive-LM/CLM (CLM-v0.1-8B head; Apache-2.0).
