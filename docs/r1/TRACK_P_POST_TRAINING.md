# Track P — Decision-Model Post-Training and Labels (technical specification)

Status: **adopted 2026-10-26 (PLAN §10 R1-C3-POST, with R1-C3-CONTROL, R1-SOFT-SIGMA, R1-PORTAL-SCHEDULE, R1-JEV-RUNG, R1-RB-TEACHER)**; proposed 2026-10-25, revised 2026-10-26 after the reference review. **Corrected 2026-10-26 (evening) by the author's Track P decisions** (PLAN §10 R1-STARTLUX-TRAINABLE, R1-E0-PROTOCOL, R1-A3-BUDGET, R1-RPS-NORM, R1-EDGES-10, R1-TIEBREAK, R1-HEADS-LN, R1-LAYA-POOL, R1-TEMPERATURE, R1-TOKEN-INIT, R1-LR-GRID, R1-ENV-PIN; and the same evening R1-E0-THRESHOLDS, R1-E0-BUDGET, R1-E0-HEADFIT, R1-CONTROL-READOUT, R1-TRACKP-CHOICES, R1-EXAM-RULE-V2); edits marked "(26 Oct, R1-…)". Execution: `docs/r1/prompts/PORTAL_TRACK_P_RUNBOOK.md`.
Supersedes the post-training part of R1-C3-BASE (24 Oct).
Scope: C3 decision models (A5 / A6), label generation, the decision-model exam, SFT, RL, DAgger, evaluation.
Runbook counterpart: `docs/r1/RUNBOOK.md` → Track P. Reading list: `docs/r1/references/README.md`. Base-model facts (Kev, StartLux, Laya) are those checked on 25 Oct and recorded in RUNBOOK Track P; P.0 confirms them.

---

## 0. Corrections to R1-C3-BASE (24 Oct)

| Item in R1-C3-BASE | Correction | Consequence |
|---|---|---|
| "StartLux plugs directly into TRL GRPO" | Not verified and probably false. StartLux-Decision v1.1 (code Apache-2.0, weights CC BY-NC 4.0): no public training code; the Instant models answer in one forward pass with bidirectional attention over the prompt, served through a vLLM plugin. | StartLux must pass a training spike in plain transformers with the correct prompt mask (P.0). If it fails, it becomes an inference-only zero-shot rung (owner decision). |
| Kev as a ready RL target | Kev (`jaredpalmer/kev`, Apache-2.0): rank-16 LoRA on Qwen3.5 hybrid bases (attention, MLP and DeltaNet projections) plus a pointer head scoring each option's `</opt>` state against the question's `<decide>` state; one question per row; trainer takes one hard label per question, no RL code. | Kev is wrapped by our own loop (patched trainer or `kev/model.py`). Hard-label training is not used: argmax-style targets collapse outcome distributions into step functions (§10, R1/R2). |
| Laya soft-label support | Laya (`NandhaKishorM/laya`, Apache-2.0): ModernBERT-large **encoder**, 421M, 1,024-token context, typed-decision head; fine-tune notebooks ("RLCD": RL against strictly proper scoring rules) with temperature calibration per option count. Soft-label support undocumented. | Wrapped by our loop with soft targets; prompts must fit 1,024 tokens. Laya cannot generate text, so it is not eligible for the reasoning arm R-B. On a head output, RL against a proper score has the same optimum as SFT with that score (§0.1), so its RLCD notebook serves as a cross-check of our loop, not as a separate stage. |
| TRL as the training backbone | Dropped. | One shared PyTorch + PEFT loop for all models (§4). |
| A6 = "12 bins as 12 actions, maximise expected reward + KL to SFT" | Structurally conflicts with calibration: the maximiser of expected reward over discrete actions is a point mass, so the belief stops being a probability; the KL term only slows the collapse. A smoothed-rule variant (belief → rule → utility) still lets the decision term distort the belief near the threshold. | **Belief and action are separate outputs** (§2, §6.3). The belief is trained only with a bounded proper scoring rule; the action is trained with the decision reward. Follows the RLCR argument (§10, R4). |

### 0.1 Why RL is not automatically useful here

Soft-label cross-entropy (log score) and RPS are proper scoring rules. On the same offline labels, RL with a proper-scoring reward has the **same optimum** as SFT, with a higher-variance gradient estimator. RL is therefore used only where at least one of the following holds:

1. the objective differs (decision utility rather than predictive score) → action head, Stage R-A;
2. the output is not differentiable (the model reasons in text before answering) → Stage R-B;
3. the state distribution differs (on-policy states after the configurator changes the loop) → Stage D.

RL on the same base also mainly **sharpens** the base distribution rather than adding capability (§10, R5). Expected effects of RL are therefore stated as calibration/decision-quality changes, not capability gains.

### 0.2 Reward rules (all stages)

- Rewards and losses that touch the **belief** are bounded proper scores only: RPS (primary) or Brier. CE (log score) is allowed in supervised Stage S but **never inside an RL reward** — an unbounded score can dominate and collapse the policy (RLCR's log-score variant collapsed to 0 % accuracy).
- The decision reward acts **only on the action output**, never on the belief.

---

## 1. Problem framing (DAC)

| DAC element | Paper B |
|---|---|
| Target algorithm | Governed autoresearch loop (proposer + executor + acceptance rule) |
| Instance *i* | (task node, instance seed) |
| Step *t* | One proposal |
| State *s_t* | Proposal diff/text, incumbent, budget used/remaining, acceptance history, node noise level σ_node |
| Action *a_t* | skip / execute; after execution keep / reject |
| Reward | Δ_audit · keep − g · execute |
| Policy | Belief *p_θ(· | s_t)* over 12 increment bins, plus either the C2 theory rule applied to the belief or a learned action head |

Positioning note for the manuscript: the single-proposal decision is a contextual bandit; the full loop is DAC because (a) the optimal threshold depends on remaining budget and (b) the proposer reacts to accepted history. Stage D (DAgger) is the empirical evidence for (b).

---

## 2. Model wrapper and output contract

### 2.1 Outputs

Every model is wrapped to expose two outputs per proposal:

| Output | Shape | Trained by | Used for |
|---|---|---|---|
| **Belief** *p* | 12 logits → distribution over increment bins | Bounded proper score only (RPS, + CE in Stage S) | C3 prior; theory rule; calibration metrics |
| **Action** *π* | 1 logit → P(execute) | Decision reward only (§6.3) | Learned-policy arm; compared with rule(belief) |

The action head is optional (absent in Stage S and in the "rule-on-belief" arm).

### 2.2 Wrapper types

| Wrapper | Used by | Belief readout | Action readout |
|---|---|---|---|
| `PointerWrapper` | Kev | Kev's pointer head over 12 bin options (`</opt>` states vs the `<decide>` state); fixed bin names and order; built-in pointer temperature fixed at 1 in training (26 Oct, R1-TEMPERATURE) | LayerNorm + Linear (hidden → 1) on the `<decide>` state |
| `HeadWrapper` | Laya (typed-decision head), StartLux (option readout; trainable, 26 Oct, R1-STARTLUX-TRAINABLE), optional others | The family's own 12-option readout | LayerNorm + Linear (hidden → 1) on the question/decision state; for Laya the encoder output mean-pooled over valid tokens (26 Oct, R1-LAYA-POOL) |
| `BinTokenWrapper` | Qwen3.5-0.8B/4B-Base control | LM-head logits restricted to 12 reserved tokens `<b0>…<b11>` at the belief position | LM-head logits on `<exec>` vs `<skip>` at the action position |
| `ReasonThenBinWrapper` | Stage R-B only (generative bases: Qwen control, Kev's base LM) | As BinTokenWrapper / PointerWrapper, after a sampled `<analysis>` span | As above, after the belief |

Shared serialisation: one text template, ≤ 1,024 tokens (Laya's limit), fixed bin names and order.

Every new head (action, cumulative, the E0 linear belief head) reads a LayerNorm-ed state (26 Oct, R1-HEADS-LN). The reserved tokens `<b0>…<b11>`, `<exec>`, `<skip>` are initialised from the mean of the existing token embeddings; those rows are kept and trained in fp32 at a lower lr, 1e-4 (26 Oct, R1-TOKEN-INIT; value confirmed by R1-TRACKP-CHOICES).

### 2.3 Belief head form (exam factor)

- **Softmax-12**: one softmax over bins 0–11 (default).
- **Cumulative-11**: bin 0 as a Bernoulli (no-op); **10** threshold sigmoids *P(z > e_k)*, one per finite edge between bins 1–11, made monotone (cumulative max over sorted edges) and differenced into bins — 1 + 10 = 11 outputs (26 Oct, R1-EDGES-10; the earlier "11 threshold sigmoids" was wrong: 11 bins have 10 finite edges). This is "one Noul per bin edge" and maps directly onto threshold decisions.
- The cumulative form is a hypothesis to test, not a conclusion: Jev's Noul behaviour (§10, R1) may come from its training, not its head form.

### 2.4 Tree packing

One sequence holds one loop state and *Q* proposal branches: `[state | branch_1 | … | branch_Q]`.

- Attention mask: *M_ij = 1[j ≤ i] · 1[g_j = 0 ∨ g_j = g_i]* (g = 0 for state tokens, g = q for branch q). Branches see the state and themselves, never each other.
- Position ids: tree depth *pos_i = |anc(i)|*, i.e. every branch restarts at position *S*. With packed-index positions, outputs depend on branch order (§10, R1 numpy demo); with tree-depth positions they do not.
- Readout at each branch's last token.
- Requirement: the model accepts a custom 4D attention mask and explicit position_ids (checked in P.0 / E4). Models that fail train unpacked (one proposal per sequence).
- Scope: packing is an efficiency option, not a selection criterion. Qwen3.5 hybrid bases (Kev, the control) contain DeltaNet linear-attention layers that cannot take an arbitrary mask, which is why Kev runs one question per row; expect them to train unpacked. For the encoder (Laya) the analogous mask is state ↔ state and branch → state + own branch; the 1,024-token limit leaves little room for packing anyway. Packing matters mainly for StartLux and any full-attention extra candidate.

### 2.5 Interface

```python
class DecisionModel(nn.Module):
    def forward(self, packed_batch) -> dict:   # {"belief_logits": [N_branches, 12], "action_logit": [N_branches] | None}
    def trainable_parameters(self) -> Iterator[Parameter]
    def save(self, path) / load(self, path)     # adapter + heads only
```

Bin 0 is the no-op bin. Bins 1–11 cover the standardised increment *z* (§3.3).

---

## 3. Labels

### 3.1 Source

- Sweep 1: ≈ 5,800 proposals. Inert and duplicate proposals removed → ≈ 2,000 audited proposals.
- Host: deepthought (no mixing hosts within one table).
- Each audited proposal is run with **10 fresh seeds**:
  - 7001–7005 → **training labels** (`y_train`)
  - 7006–7010 → **evaluation labels only** (`y_eval`)
- The two seed blocks are never mixed in any quantity used for training, model selection, threshold tuning, or the oracle ceiling's construction. The 19 Oct pilot "gate pass" was an artefact of mixing them.

### 3.2 Increment

For proposal *j* on instance *i* and seed *r*: Δ_{j,r} = metric(incumbent + edit_j, seed r) − metric(incumbent, seed r) (paired on seed, sign oriented so that larger is better).

### 3.3 Standardisation and bins

- Standardise by the node noise floor: *z = Δ / σ_node*, with σ_node from the C1 30-seed noise-floor table (pooled per node). This makes bins mean the same thing across nodes, which LONO requires.
- Default bin edges for bins 1–11 in *z* units (confirm against the R1-C3-BASE bin table; if that table already fixes edges, it wins):

  `(−∞, −2, −1, −0.5, −0.25, −0.1, 0.1, 0.25, 0.5, 1, 2, +∞)`

- Bin 0 (no-op): assigned by rule to proposals whose edit is a no-op under the harness definition; these do not enter the Gaussian integration.

### 3.4 Soft label

For audited proposal *j*: μ_j = mean of *z_{j,r}* over r ∈ {7001…7005};

s_j = σ̂ / √5, where σ̂ is the **pooled** node noise σ (in *z* units σ̂ = 1, so s_j = 1/√5 ≈ 0.447 under homoscedasticity).

- Do **not** use the per-proposal 5-seed sample variance: with 4 degrees of freedom it is unreliable and makes labels arbitrarily sharp or flat. Adopted 26 Oct (R1-SOFT-SIGMA): replaces the per-proposal se_audit in `r1/c3/labels.soft_label` through a new versioned mode; the old mode stays for reproducing existing tables.
- Where K is raised for proposals near t* (RUNBOOK labels item 7), use s_j = σ̂ / √K_j with K_j the number of label seeds.
- If C1 or the audit data show heteroscedasticity by edit type, use a per-type pooled σ̂ (shrunk towards the node σ̂).
- Optional: integrate a Student-t with ν = pooled degrees of freedom instead of the normal (ν ≈ 29 from the 30-seed table → practically identical).

y_{j,k} = Φ((e_{k+1} − μ_j)/s_j) − Φ((e_k − μ_j)/s_j),  k = 1…11; y_{j,0} = 0.

The same construction with seeds 7006–7010 gives `y_eval`. **Hard (argmax) labels are never used for training.**

### 3.5 Action target

Execution utility, matching the A6 reward r = Δ_audit · keep − g · execute with g = 0.1 σ_node (22 Oct):

u_j = mean_{r ∈ label seeds} (Δ_{j,r} · keep_j) − g,

where keep_j comes from `r1/c3/rules.py` (`keep`) applied to the logged Δ̂_j under a **fixed reference prior** (A1 constant prior), so the target does not depend on the model being trained. Computed from seeds 7001–7005 for training and 7006–7010 for evaluation. For the rule-on-belief arm, the belief enters through `rules.decide(π, μ, τ, σ, g, Δ̂)` with (π, μ, τ) from `labels.moments`; a bin-level shortcut V(p) = Σ_k p_k v_k (v_k = c_k · P(keep | k)) is used only in the R-A3 ablation.

### 3.6 Splits

- Primary split by **instance seed** (train / val / test instance blocks). Val is drawn from training instances and uses `y_train` only.
- Group duplicates and near-duplicates by **edit hash across splits** (the same edit can appear under different instance seeds).
- **LONO**: leave-one-node-out folds over task nodes.
- The decision-model exam set (§5) is a fixed subset of the training partition and never overlaps the test instances.
- Tree packing groups branches **within** one split and one state; packing never mixes splits.

### 3.7 Expansion

- B.6: expand to 8–10k labels (same protocol). Decide after the learning curve (§7.3): expand only if RPS skill is still rising between the 1k and 2k points.
- C.2: one DAgger round (§6.5).

### 3.8 Label files

`data/c3_labels/{sweep}/labels.parquet`, one row per audited proposal:

| column | type | note |
|---|---|---|
| proposal_id, edit_hash, node, instance_seed, state_id | str/int | grouping keys; state_id groups branches for packing |
| prompt_ref | str | pointer to serialised state + branch |
| z_train[5], z_eval[5] | float | per-seed standardised increments |
| mu_train, mu_eval | float | |
| y_train[12], y_eval[12] | float | soft labels |
| u_train, u_eval | float | execution utility (§3.5) |
| is_noop | bool | |
| split, lono_fold, exam_member | str/int/bool | |

---

## 4. Shared training loop

- PyTorch + PEFT (LoRA), no TRL. One loop, losses plugged in per stage.
- Host: zhixu portal (1× RTX 4090 24 GB). Models ≤ 4B, bf16, gradient checkpointing.
- Default LoRA: r = 16, α = 32, dropout 0.05, targets = attention q/k/v/o + MLP up/down/gate (+ DeltaNet projections on Qwen3.5 hybrid bases, as Kev does).
- Learning rate: **one grid {1e-5, 3e-5, 1e-4} for the adapter of every family, chosen by val RPS** (26 Oct, R1-LR-GRID; replaces 2e-5 from a released adapter / 1e-4 for a fresh LoRA); released heads train at the adapter lr (Track P agent's reading); new heads 1e-3; new token rows (bin-token family) in fp32 at lr 1e-4 (R1-TOKEN-INIT, R1-TRACKP-CHOICES).
- Environment pinned (26 Oct, R1-ENV-PIN): torch 2.6.0+cu124 on driver 535; Kev code at the P.0 commit `2074cc4`, its diff to `kev-1.0` recorded.
- Batches are tree-packed (§2.4) where the model supports it: one forward pass per state with all its proposals.
- Three training seeds per configuration; report mean ± s.e.
- Every run logs: train loss, val RPS, val NLL, val ECE (all-bins and top-1), val PIT, mean predictive std vs mean label std, val decision utility, action/rule disagreement rate (when an action head exists), mass on bin tokens (BinTokenWrapper), gradient norm.

---

## 5. Decision-model exam (P.3)

Purpose: narrow the post-training set to **1–2 candidates** (plus the Qwen control as an ablation arm) before spending SFT/RL effort. Analogous to the proposer exam, but for decision models; results go to the appendix.

### 5.1 Candidate pool

Selected to span architectures, not sizes (all ≤ 4B). Record for each whether the checkpoint is **base or instruct/RLHF** (covariate; prefer base when both exist, since post-training tends to worsen probability calibration — §10, R3).

| Class | Candidate | What it tests |
|---|---|---|
| Decision-pretrained hybrid decoder + pointer head | Kev (Qwen3.5 hybrid base) | Value of decision pretraining |
| Bidirectional-in-prompt decoder | StartLux Instant — **trainable candidate** (P.0 passed; 26 Oct, R1-STARTLUX-TRAINABLE). Licence CC BY-NC 4.0 (non-commercial research use), noted in the registry and in the appendix | Prompt-bidirectional attention for reading a diff + state |
| Encoder, proper-scoring-trained decision head | Laya (ModernBERT-large, 421M, 1,024 ctx) | Small encoder vs decoders; value of prior proper-scoring training |
| Plain causal LM base (control) | Qwen3.5-0.8B-Base, Qwen3.5-4B-Base; **primary readout a fresh LayerNorm + linear head**, the bin-token readout a secondary row; bin list in the prompt in canonical order (26 Oct evening, R1-CONTROL-READOUT, amends R1-C3-CONTROL) | Same base as Kev; size effect |
| Non-LLM floor (not a finalist) | Frozen embedding model + ordinal logistic regression; GBDT on hand features | Whether an LLM is needed at all |

Optional extra slot: one further ≤ 4B architecture (e.g. a hybrid attention/SSM model) if its spike passes within the one-day budget.

**Zero-shot rungs (no training; rows in the exam and in the "LLM self-control" comparison).** These are reference points, not post-training candidates.

| Row | How the belief is elicited | Why it is there |
|---|---|---|
| Candidates' native decision interface (E1) | Kev, Laya, StartLux answer a 12-option typed question out of the box; control: bin-token logits after an instruction prompt | What each base knows before any training |
| Instruct LLM, verbalized top-k | Prompt lists all 12 bins and asks for a probability on each (top-k style; §10, R3); token logprobs are not used | Zero-shot "LLM self-control"; runs locally via llama.cpp |
| Jev (API, optional) | **10** Noul questions, one per finite bin edge ("Will z exceed e_k?"; 26 Oct, R1-EDGES-10), as branches on one shared state in one request; monotone CDF (cumulative max) → bins 1–11 (bin 0 gets no mass) | Ceiling reference: how close does a small post-trained local model get to a large calibration-trained commercial decision model? |

Jev protocol (R1-JEV-RUNG, 26 Oct; TypeSafe's official API with the author's key; proposal diffs and loop state are sent to TypeSafe):

- Base URL `https://api.typesafe.ai` (path and schema per `https://docs.typesafe.ai/api`); pin a **versioned** model name in the config (`jev-1.14.0`, R1-ENV-PIN — verify with the key that it exists before Phase 7; never `jev-latest` or `jev-preview`) and log the version the API returns, the endpoint, the request date, and the full request/response JSON per call (`results/track_p/jev/{date}/calls.jsonl`).
- Responses vary by about ±0.02 between identical requests: three repeats per state, report the mean and spread.
- Run once on the exam set and once on the final test instances; no Jev output is ever used as a training label.
- If the model string changes between runs, the rows are reported separately.

### 5.2 Prerequisites

- P.0 spikes passed (load, LoRA attach, a few soft-label steps, save/reload round-trip with identical logits).
- E0 and E6 need **no audit labels** and run right after P.0.
- E1–E5 need labels and start once the first ≈ 400–500 training-partition proposals have `y_train`.

### 5.3 Exam set

- ≈ 400–500 audited proposals from the training partition, ≥ 3 nodes, frozen as `exam_member = True`.
- Internal split 70 / 30 by instance seed (grouped by edit hash). Labels: `y_train` only. `y_eval` and test instances are not touched.

### 5.4 Tests

| ID | Test | Labels needed | Metric | Cost per model |
|---|---|---|---|---|
| **E0** | Aleatoric pass-through (synthetic, §5.5) | none (synthetic) | held-out RPS; width slope vs the label's own std; hard-label collapse contrast | ≈ 1–2 h (v2: to convergence, lr grid) |
| E1 | Zero-shot (generative models and zero-shot tier): format compliance and RPS | exam set | compliance %, RPS skill | minutes |
| E2 | Frozen linear probe: belief head on frozen last-token features, trained to convergence | exam set | val RPS skill | < 15 min |
| E3 | Short LoRA SFT: fixed budget (300 steps, same lr schedule and LoRA config for all), 3 seeds; softmax-12 head | exam set | val RPS skill, all-bins ECE, top-1 ECE, PIT, width ratio, seed spread | ≈ 1 h |
| E4 | Engineering: peak VRAM, step time at 1,024 tokens and batch 8, save/reload determinism; tree-packing support (custom 4D mask + position_ids) recorded, not scored | none | numbers, pass/fail | measured during E3 |
| E5 | Calibration after temperature scaling (one scalar T fitted on dev, the same procedure for every model, Kev included; R1-TEMPERATURE) | exam set | all-bins ECE | seconds |
| **E6** | Architecture probes (§5.6) | none (synthetic + exam prompts, outputs only) | pass/fail per probe | < 30 min |
| E7 | Head form: softmax-12 vs cumulative-11, run on the top 2 after E3 only | exam set | E3 metrics | ≈ 1 h each |

RPS skill = 1 − RPS_model / RPS_base-rate, where the base-rate predictor is the mean `y_train` of the exam-train portion. Width ratio = mean predictive std / mean label std (≈ 1 is right; ≪ 1 is collapse).

### 5.5 E0 — aleatoric pass-through test

The task-specific analogue of the biased-coin probe (§10, R1/R2): can the architecture read a stated mean and noise level and output a distribution of the right **location and width**?

- Synthetic prompts in the same serialisation as real states, with a line such as "expected standardised increment m = 0.3, noise s = 0.6" embedded among realistic distractor fields.
- Grid: m ∈ [−2.5, 2.5], s ∈ [0.1, 1.5]; ≈ 3,000 train / 1,000 test prompts; test (m, s) cells held out from training (interpolation and mild extrapolation cells).
- Target: soft label = N(m, s²) integrated over the 12 bins (bin 0 never active).
- **Protocol v2 (26 Oct, R1-E0-PROTOCOL; replaces "frozen backbone, then 200 LoRA steps" and the released-head fit):**
  - A **fresh LayerNorm + linear belief head** (hidden → 12) for every model, on the readout state its action head reads (lr 1e-3 when it trains with LoRA).
  - **Head fit (descriptive only; 26 Oct evening, R1-E0-HEADFIT):** cached frozen-backbone features, full-batch L-BFGS of the train RPS to convergence on CPU; it initialises the head of the LoRA stage. (The fit is non-convex — LayerNorm's affine times the linear layer — so "convergence" is a stationary point: two outer L-BFGS steps without relative improvement > 1e-9, the history reset in between.)
  - **Budget, two stages, the same for every model (R1-E0-BUDGET):** (1) **lr screen** — LoRA + head on the grid {1e-5, 3e-5, 1e-4}, ≤ 2,000 steps, evaluation every 100, early stopping (patience 5, the Track P agent's value), the lr with the lowest best val RPS selected; (2) **one run at the selected lr**: cap 6,000 steps, evaluation every 100, patience 10, best checkpoint restored. **The E0 metrics come from that run.** The hard-label contrast and the native-readout run reuse the selected lr with the stage-2 budget.
  - Validation cells (1,3), (3,2), (5,4), (8,2), (0,3), (9,3) are held out of the training grid and are disjoint from the held-out test cells; the starting model of a LoRA stage counts as an early-stopping candidate; the Qwen control's token rows stay frozen in the fresh-head run (confirmed, R1-TRACKP-CHOICES).
  - **Released heads are reported separately** (the family's native readout: zero-shot, then the same LoRA stage).
  - Contrast run: identical, but with **hard argmax labels**.
- Metrics on held-out cells: RPS; **width slope = regression slope of the predicted std on the label's own std** (the binned soft label's std with the same bin representatives; target 1), with the **label's own slope vs s reported as the ceiling**; slope of predicted mean on m (target 1); the v1 slope of predicted std on s is still reported; for the hard-label run, width ratio (expected to collapse).
- **Pass (a floor, not a ranking; 26 Oct evening, R1-E0-THRESHOLDS):** width slope vs the label's own std **≥ 0.6** with its **bootstrap 95 % lower bound > 0** (2.5th percentile of 2,000 resamples of the 1,000 test prompts — resampling unit chosen by the Track P agent), and mean slope **≥ 0.8**, on the soft-label stage-2 run. Frozen in `r1/c3/rules/p3_rule_v2.yaml`. The soft-vs-hard contrast is an appendix figure.

### 5.6 E6 — architecture probes

Adapted from the Jev probe set (§10, R1). All on the soft-label E0 model unless stated.

| Probe | Construction | Pass criterion |
|---|---|---|
| A1 Branch isolation | Same branch scored alone vs packed with 7 siblings | max |Δ logit| ≤ 1e-3 (bf16 tolerance); packed models only |
| A2 Sibling-order invariance | Permute sibling order (5 permutations) | max |Δ logit| ≤ 1e-3 |
| A3 History-length robustness | Prepend irrelevant acceptance history at **0 / 25 % / 50 % / 100 % of the remaining token budget**, under the smallest context limit in the pool (1,024 tokens) for every model, so the same text fits every model (26 Oct, R1-A3-BUDGET); 2k / 8k descriptive only | mean |Δ RPS| ≤ 0.01 |
| A4 Width monotonicity | Same prompt, s increased in 5 steps; reference = the label's own std at each step (26 Oct, R1-E0-PROTOCOL) | predicted std non-decreasing wherever the label's std increases, on **≥ 95 % of prompts** (R1-E0-THRESHOLDS; recorded under E6, not disqualifying — §5.7.1) |
| A5 Slot bias | BinTokenWrapper: permute the order bin tokens are listed in the prompt (canonical order otherwise) | **descriptive only**, read on the readout used for selection (for the Qwen control the fresh head; 26 Oct evening, R1-CONTROL-READOUT); TV distance reported against the former 0.02 |

### 5.7 Pre-registered selection rule

1. Discard models that fail E0, or fail E4 hard limits (OOM at 1,024 tokens, batch 8 with grad checkpointing; non-deterministic reload). E6 failures are recorded; A1/A2 failures disable packing for that model but do not disqualify it.
2. Rank by E3 mean val RPS skill. Paired bootstrap over instances (2,000 resamples) against the top model.
3. Models not significantly worse than the top (95 % paired bootstrap interval of the difference includes 0) form the tied set.
4. **Finalist 1 = the E3 point-estimate top** (26 Oct evening, R1-EXAM-RULE-V2; supersedes R1-TIEBREAK).
5. **Optional second finalist**: among the tied models of a different architecture class than finalist 1, picked by the tie-break order on point estimates — higher E2 probe skill (models within an RPS-skill difference ≤ 0.01 are tied on E2), then smaller |width ratio − 1|, then base over instruct, then lower cost (E4); a tie left after all four goes to the model name (Track P agent's rule). Rule v2: `r1/c3/rules/p3_rule_v2.yaml`, frozen with its sha256; `exam_analyze` accepts v2 only. The Qwen control (size chosen by E3) is always carried as the ablation arm and does not count towards the 1–2.
6. E7 decides the head form for the finalists.
7. If no LLM beats the non-LLM floor by a significant margin on E3, stop and escalate (this changes the paper's story).

Caveat recorded in the appendix: the exam set is small, so ranking is coarse; it is a screening step, not a result.

---

## 6. Stages

### 6.1 Stage S — SFT (A5), belief only

- Loss: L_S = RPS(p_θ, y_train) + CE(p_θ, y_train). Both are proper; RPS respects bin order, CE keeps sharp gradients early. Ablation: CE only.
- RPS(p, y) = 1/(K−1) · Σ_{k=1}^{K−1} (P_k − Y_k)² over the cumulative distributions of the K = 11 ordered bins 1–11 (10 terms; 26 Oct, R1-RPS-NORM), on the non-inert parts; bin 0 is a separate Bernoulli term (Brier), and RPS = ½ · (Brier₀ + (1 − y₀) · ordinal part), in [0, 1] (`r1/c3/train/metrics.rps`).
- lr as in §4 (adapter grid {1e-5, 3e-5, 1e-4} chosen by val RPS, 1e-3 new heads), cosine, warm-up 5 %, effective batch 16, ≤ 5 epochs, evaluation every ¼ epoch.
- Kev's trainer is patched (or bypassed via `kev/model.py`) to accept soft targets.
- Output: the A5 table (B.5).
- Early stopping on val RPS, patience 2 evaluations. **Select the best checkpoint, not the last.**
- Post-hoc temperature scaling on val → calibration baseline (the same procedure for every model; R1-TEMPERATURE).

### 6.2 RL gate (all must hold)

1. val RPS skill of the selected SFT checkpoint is significantly > 0 (paired bootstrap vs base rate). If not, stop: RL will not recover it, and the negative result is reported.
2. Output stable: BinTokenWrapper mass on the 12 bin tokens > 99 % on val; no NaN/collapse across 3 seeds.
3. val all-bins ECE ≤ 0.05 (after temperature scaling) — threshold to be confirmed on the first SFT run.
4. val width ratio ∈ [0.8, 1.25].

### 6.3 Stage R-A — decoupled action head (A6, redefined)

Head models (Kev, Qwen control, StartLux if trainable). Exact objectives; no sampling needed.

**Arms**

| Arm | Belief | Action | Purpose |
|---|---|---|---|
| R-A0 rule-on-belief | Stage S belief | execute iff V(p) = Σ_k p_k v_k > g | Theory policy with learned prior (main C3 arm) |
| R-A1 action head, detached | Stage S belief (frozen) | Linear action head on **stop-gradient** hidden state | Learned policy without touching the belief |
| R-A2 action head, shared | Belief keeps training with RPS | Action head; its loss also updates the shared LoRA | Learned policy with shared representation |
| R-A3 smoothed rule (ablation) | RPS − λ · a_τ(p) · u | none | Former A6 proposal; shows belief distortion |

**Losses**

- Belief (R-A2): L_belief = RPS(p, y_train). No decision term.
- Action (R-A1, R-A2): with execution utility *u* from §3.5 and π = P(execute),

  L_action = −E[π · u] = −π · u, implemented as cost-sensitive BCE: target 1[u > 0], weight |u|.

  The belief stays proper because the decision reward never reaches the belief output (RLCR's decoupling argument, §10, R4). In R-A2 the shared LoRA can still shift the belief indirectly; the belief's own loss remains proper, and the width ratio and ECE are monitored for drift.
- R-A3 (ablation only): L = RPS(p, y) − λ · a_τ(p) · u, a_τ(p) = sigmoid((V(p) − g)/τ), τ annealed 0.5 → 0.05, λ ∈ {0.1, 0.3, 1, 3}.

**Deployment**: an A6 arm is served as rule(belief) (R-A0) or as the action head (R-A1/2), never as the greedy bin (this replaces "deploy the greedy bin" in the 25 Oct P.4).

**Key metrics**: decision utility of each arm; **disagreement rate** between the action head and rule(belief) — the direct measurement of "learned policy vs theory policy on the same belief"; belief ECE/width drift vs Stage S.

**GRPO estimator check (unit test, not a contribution).** On R-A1: sample execute ~ Bernoulli(π), reward r = u · execute, group size 8, group-normalised advantage. Over a fixed batch of 256 prompts, the GRPO gradient must match the exact gradient of L_action with cosine ≥ 0.95 (averaged over 64 resamples). This validates the RL machinery before R-B, where no exact gradient exists.

### 6.4 Stage R-B — reasoning arm (GRPO), belief and action decoupled

This is the "LLM self-control" arm of the self-control vs trained-configurator vs hybrid comparison.

- Eligible models: only bases that can generate text — the Qwen control and Kev (its Qwen3.5 base LM writes the analysis; the pointer head reads the belief). Laya (encoder) and StartLux Instant (single forward pass) are not eligible.
- Output format: `<analysis> … </analysis>` (≤ 256 tokens, sampled) → belief position (bin-token or pointer logits read, not sampled) → action token `<exec>` / `<skip>` (sampled). The 256 analysis tokens come on top of the ≤ 1,024-token prompt.
- Warm start:
  1. Stage S checkpoint (belief without analysis);
  2. SFT warm-up on ≈ 500 training-partition examples with a demonstration analysis each (RLCR used ≈ 500 such examples). A 0.8–4B base has never produced this format, so it first learns it by imitation. The demonstrations are written by **DeepSeek-V4.1-Flash-1017 via the DeepSeek API** (`deepseek-flash`; author decision 26 Oct), which sees exactly the serialised view the decision model sees (same leak-guarded state + proposal) and **never the labels, audit results, siblings or future fields**, so analyses cannot leak outcomes. Log the model version returned in every response (the `deepseek-flash` alias can move), prompts and outputs (`results/track_p/rb_demos/{date}/calls.jsonl`); run in off-peak hours. Estimated cost for 500 demonstrations: well under USD 5 even with long reasoning traces. Note: this makes R-B a distilled arm (a larger teacher's reasoning style), which is reported as such. SFT targets: the demonstration analysis, `y_train` (belief) and 1[u > 0] (action).
  3. Fallback if warm-up analyses are not produced: format-only SFT (short template analysis) and report R-B as "without warm-up".
- Reward (computed from the label distribution, never a single seed draw):

  r = −RPS(p, y_train) + λ_a · 1[action = exec] · u − 0.5 · 1[format violation]

  RPS is bounded (≤ 1); u is clipped to [−u_max, u_max] with u_max from the 99th percentile on train. No log score in the reward (§0.2).
- Gradient path: policy gradient through sampled tokens (analysis + action); the belief term's dependence on the analysis also goes through the policy gradient; the belief logits at the read-out position additionally receive the exact RPS gradient.
- GRPO: group size 8 (16 if memory allows), KL to the warm-started policy β ∈ {0, 0.02}, LoRA r = 16, lr 1e-6 → 5e-6, ≤ 500 steps.
- Report the same disagreement rate as R-A (action vs rule applied to the model's own belief), and the R-B analysis ablation (with vs without `<analysis>`).

**Stop rule (R-A2, R-A3, R-B).** Roll back to the best checkpoint if any of:
- val all-bins ECE rises > 0.02 above the Stage S checkpoint;
- val RPS worsens by > 1 s.e. while val decision utility has not improved;
- val width ratio drops below 0.8 (sharpening, §10, R5);
- mean predictive entropy falls > 20 % below Stage S within 100 steps.

### 6.5 Stage D — DAgger (C.2)

1. Run the loop with the current configurator on fresh training instances.
2. Collect states the configurator visits; audit the newly proposed edits with the same 10-seed protocol (7001–7005 for labels).
3. Aggregate with existing labels; retrain from the Stage S recipe (and the selected R-A arm).
4. One round in C.2; report the shift in proposer behaviour (acceptance-history feedback) as evidence of the sequential (DAC) structure.

---

## 7. Evaluation

### 7.1 Offline (test instances, `y_eval` only)

- Belief: RPS skill, NLL, **all-bins ECE and top-1 ECE** (top-1 alone can look good while the distribution has collapsed), PIT histogram, width ratio.
- Decision: utility U and **gap closed** = (U_model − U_base) / (U_oracle − U_base):
  - U_base: theory rule with the base-rate belief.
  - U_oracle (noisy-oracle ceiling): theory rule with belief built from `y_train` of the **same** proposal, evaluated against `y_eval`.
- Action/rule disagreement rate for every arm with an action head.
- Ladder: base rate → non-LLM floor → zero-shot tier (Jev Noul-CDF, verbalized top-k) → Qwen control → finalist(s) (R-A0) → R-A1/R-A2 → R-B arm.

### 7.2 Generalisation

- LONO folds: all metrics per held-out node.
- Ablations: Qwen base + LoRA vs Kev (same base) isolates decision pretraining; softmax-12 vs cumulative-11 head; soft vs hard labels (E0 + one real-label run).

### 7.3 Learning curve

Train on 250 / 500 / 1k / 2k (and 8k after B.6) labels; plot test RPS skill and gap closed. This decides B.6.

### 7.4 Closed loop (main table)

Fixed budget, fresh instances, ≥ 3 harder benchmarks where available. Compare: theory index (base-rate belief), trained belief + theory rule (R-A0), learned action head (R-A1/2), LLM self-control (R-B and zero-shot tier), hybrid. Report final quality and number of executions.

---

## 8. Compute and cost notes

- Training is cheap: ≤ 4B LoRA on ≈ 2k examples is minutes to an hour per run on the 4090; tree packing cuts forward passes further.
- E0 and E6 are label-free and can run while the label sweep is still going.
- The cost driver is **auditing**: ≈ 2,000 × 10 training runs on deepthought. Estimate total time from per-node run length before committing to B.6's 8–10k.
- Jev zero-shot rows cost API calls; one request per state (10 Noul branches × proposals; R1-EDGES-10).

---

## 9. Open items

- Confirm bin edges and the no-op definition against R1-C3-BASE.
- Confirm v_k (keep probability per bin) from the C2 theory.
- Confirm ECE gate value after the first SFT run.
- StartLux tier decided 26 Oct: trainable candidate (R1-STARTLUX-TRAINABLE).
- E0 and A4 thresholds of protocol v2: decided 26 Oct evening (R1-E0-THRESHOLDS); frozen with the exam rule in `r1/c3/rules/p3_rule_v2.yaml` (R1-EXAM-RULE-V2; StartLux no longer pending). `exam_analyze` accepts rule v2 only and E0 records of protocol v2 only.
- Decided 26 Oct: Jev rung via the official API (R1-JEV-RUNG); R-B demonstrations by DeepSeek-V4.1-Flash-1017 (R1-RB-TEACHER); pooled σ̂ (R1-SOFT-SIGMA); Qwen control adopted (R1-C3-CONTROL); card schedule (R1-PORTAL-SCHEDULE).
- Track H.8 `OfflineBanditEnv` defines action = bin; under belief/action decoupling the environment action should be execute/skip (keep from the rules), with the 12-bin belief as the model's forecast. Track H was accepted on 26 Oct with action = bin, so an H.8 amendment is needed before P.5 uses the environment (owner: Dow).

---

## 10. References and what Track P takes from them

PDFs and notes in `docs/r1/references/` (see its `README.md`).

**R1. Jev architecture reconstruction (internal PDF, `docs/r1/references/jev_architecture-v2.pdf`) and A. Hume, "Jev's Architecture, Unmasked" (17 Sep 2026).**
Jev is TypeSafe's decision API: shared state, typed questions (Choice ≤ 255 options, Noul binary, Score ≤ 10 ordered levels), probabilities read from hidden states rather than generated. The reconstruction: state encoded once; each question an isolated branch (tree mask *M_ij = 1[j ≤ i]·1[g_j = 0 ∨ g_j = g_i]*); tree-depth position ids make each branch identical to `[state | question]` alone (packed-index positions change outputs by up to 1.8 in the numpy demo; tree-depth positions ≈ 1e-15); readout head at the branch's last token; the returned "confidence" is a normalised p_max margin, not P(correct). Probes on jev-1.13: sibling questions invisible; target unaffected by 400 irrelevant sibling questions; options interact (an irrelevant fifth option shifts log-odds, so IIA fails); option order and slot position matter; repeated requests vary by about ±0.02. Calibration: MMLU top-1 ECE ≈ 0.03; on a biased-coin probe Noul tracks the stated base rate while Choice{heads, tails} is a step function at 50 %. Internals are inferred, not confirmed.
→ Track P: tree packing and tree-depth positions (§2.4); separate readout heads (§2.1); cumulative-11 head as "Noul per edge" (§2.3); probes A1–A5 (§5.6); E0 as the biased-coin analogue (§5.5); Jev Noul-CDF zero-shot row (§5.1); never use a "confidence" statistic in place of the distribution.

**R2. `calibration.ipynb` (wdkns/modern_genai_bilibili, `llms/架构/jev`; notes in `docs/r1/references/jev_calibration_notes.md`).**
Brier, ECE and reliability diagrams; all-options vs top-1 binning (Jev-1.13 MMLU zero-shot: 0.011 vs 0.022); the biased-coin comparison (Jev Noul vs Jev Choice vs Qwen instruct P(Yes)); prior-shift correction and Platt scaling.
→ Track P: report all-bins and top-1 ECE plus PIT and width ratio (§7.1); hard-label contrast in E0.

**R3. Tian et al., "Just Ask for Calibration", EMNLP 2023.**
For RLHF'd models, verbalized probabilities are better calibrated than token/sample probabilities; asking for several candidates with probabilities (top-k) works best (e.g. SciQ, gpt-3.5: ECE 0.256 → 0.065); chain-of-thought did not help verbalized calibration. Background reported alongside: GPT-4 MMLU ECE 0.007 pretrained vs 0.074 after PPO.
→ Track P: verbalized top-k zero-shot row instead of logprobs for instruct models (§5.1); base-over-instruct covariate and tie-break (§5.1, §5.7).

**R4. Damani et al., "Beyond Binary Rewards: Training LMs to Reason About Their Uncertainty" (RLCR), arXiv 2507.16806.**
Reward = correctness + Brier on a separately verbalized confidence. Theorem: with a bounded proper scoring rule, the optimum is the most likely answer with its true success probability; with the unbounded log score, the policy can collapse (0 % accuracy, always abstaining). Qwen2.5-7B, GRPO without KL, 32 samples, lr 1e-6–5e-6. HotpotQA in-domain ECE 0.37 (RLVR) → 0.03 (RLCR) at similar accuracy; OOD calibration improves but stays high in absolute terms. Uncertainty analysis before the confidence helps calibration, more so for smaller models.
→ Track P: belief and action as separate outputs with separate rewards (§2.1, §6.3, §6.4); bounded scores only in RL rewards (§0.2); `<analysis>` span and ~500-example warm-up in R-B (§6.4).

**R5. Yue et al., "Does Reinforcement Learning Really Incentivize Reasoning Capacity in LLMs Beyond the Base Model?", NeurIPS 2025, arXiv 2504.13837.**
RLVR improves pass@1 but base models win at large k; RL outputs concentrate in the base model's low-perplexity region; per-question accuracy is pushed towards 0 and 1; six RL algorithms behave similarly; distillation, unlike RLVR, can add new patterns.
→ Track P: select bases by base potential (E2/E3, not zero-shot alone; §5.7); frame RL gains as sharpening/calibration effects (§0.1); width-ratio and entropy stop rules (§6.4).
