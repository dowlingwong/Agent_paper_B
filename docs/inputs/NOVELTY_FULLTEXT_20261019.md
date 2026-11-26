# Paper B novelty, full-text read of the four nearest 2026 papers (2026-10-19)

*AI-assisted (Claude): an overnight subagent run on 2026-10-19 for the author, using WebSearch and WebFetch. No human has reviewed it. It follows `NOVELTY_SWEEP_PART2_20261018.md` and does not repeat it. Nothing here is evidence for Paper B.*

## 0. Access and reliability

| Paper | Source actually read | Coverage |
|---|---|---|
| SAGE, arXiv 2609.36043v1 | arXiv HTML (`arxiv.org/html/2609.36043v1`) | Full text. The arXiv PDF returned no machine-readable text. |
| FOREAGENT, arXiv 2601.05930v2 / ACL 2026 long 182 | ACL Anthology PDF (`aclanthology.org/2026.acl-long.182.pdf`), plus arXiv HTML v2 for §1–§4 | Full text, but Table 15 (top-k ablation) and the per-model cells of Table 2 could not be parsed. The arXiv HTML stops after the §4 tables. |
| Beneath the Diff, arXiv 2609.00077v1 | arXiv HTML (§1–§4.1 only, truncated) and arXiv PDF (§4.2 to the end) | Full text. Appendix bodies were read only where the fetch summary quotes them. |
| Visible but Not Avoided, arXiv 2610.15738v1 | **arXiv abs, HTML and PDF all refused (HTTP 429, proxy rate limit), as on 18 Oct.** The text was read from the alphaXiv mirror (`alphaxiv.org/abs/2610.15738.md`). | Main text and the Limitations section. Appendices F–I are missing, Tables 10–13 are partial, and the text ends mid-caption of Fig. 6. |
| Smith & Winkler 2006; Chick & Frazier 2012; Xie & Frazier 2013 | IDEAS/RePEc abstract pages | Abstract only |
| Blum & Hardt 2015 (Ladder) | arXiv abs plus PMLR v37 PDF (`proceedings.mlr.press/v37/blum15.pdf`) | Algorithm 1, Definition 2.1, Theorem 3.1 |

**Caveat on quotes.** WebFetch returns text through a summarising model. Quotes below are as returned, and short paraphrases are marked as such. Before any quote goes into the manuscript, check it against the PDF. Direct `curl` to arxiv.org was blocked by the egress proxy from both the container and the Mac VM.

---

## 1. SAGE: "A Statistical Acceptance Gate for Self-Evolving Agents" (Wang, Xia, Liu, Zhang, Wu, Yang, He, Guo, Lei; arXiv 2609.36043v1, 28 Sep 2026)

**Setting and loop (§1, §3.1).** An LLM agent improves a persistent *skill document* (text), following SkillOpt [3]. At step t the gate receives the incumbent skill S^(t) and a mini-batch of b candidate edits S̃_n = S^(t) + e_n (Eq. 1). Each candidate is scored with a frozen target model and a **binary verifier** v(S, x) ∈ {0, 1} on a held-out validation set D. The generator is fixed to SkillOpt: the paper studies the gate only.

**Noise model.** The noise is finite-sample validation error. Paired evaluation on the same items holds item difficulty fixed, but "stochastic execution noise may remain" (§3.3). There is **no explicit noise model and no measurement of σ**. Seeds, repeats and variance across runs are not reported. b, |D|, test size and step count are not stated; §4.1 says only that the setup "follows SkillOpt".

**Acceptance mechanism (§3.3, Eq. 2–11).**
- Baseline g₀: accept iff the aggregate J_D strictly improves (Eq. 2–3).
- Paired counts: w = items where the candidate is right and the incumbent wrong; ℓ = the reverse (regressions); n_S = items the incumbent solves (Eq. 4–6).
- Δ_λ = w − λℓ with λ ≥ 1; ρ = ℓ/n_S (Eq. 7).
- Population form: G_λ = Pr(W) − λPr(L) > 0 ⇔ q = Pr(W | discordant) > q_λ = λ/(1+λ) (Eq. 8–9).
- Test: with m = w + ℓ, p_λ = Pr[Bin(m, q_λ) > w] (Eq. 10). At λ = 1 this is the one-sided exact McNemar test.
- Commit iff Δ_λ > 0 **and** p_λ < α **and** ρ ≤ τ; otherwise abstain and keep S^(t) (Eq. 11). (λ, α, τ) = (1, 1, 1) recovers g₀, so every SAGE accept is also a g₀ accept. The values of λ, α, τ are tuned on held-out data and not reported.
- *Observation, not a claim of the paper:* as written, Eq. 10 uses ">" rather than "≥", which makes the test slightly anti-conservative (8 wins and 0 losses gives p = 0). The m = 0 convention stated in the text (p = 1) is also inconsistent with Eq. 10.

**Optimizer's curse.** The abstract says the naive gate "is vulnerable to the Optimizer's Curse, since the best observed score on a finite and noisy validation set is upward biased". §1 cites Smith & Winkler [7]. **No theorem or bound:** the argument is informal, and the support is empirical (the regression and score tables).

**Experiments (§4).**
- Benchmarks: LiveMath, SpreadsheetBench, SearchQA, OfficeQA Pro, ALFWorld.
- Backbones: DeepSeek-V4(-flash), GLM-5.2, MiniMax-M3, Qwen3.6, giving 20 settings.
- Baselines: vanilla SkillOpt (g₀); "C1" = paired item comparison without the test (ablation); full SAGE. The matched budget is equal proposed edits and equal tokens.
- Table 1, regression rate naive → SAGE: LiveMath 27.5–39.4 % → 0.0; OfficeQA 38.7–45.6 % → 0.0; SSB 13.5–20.2 % → 0.0; SearchQA and ALFWorld 2.4–9.6 % → 0–5.1 %. Lower in 19 of 20 settings; the tie is GLM-5.2 on SearchQA.
- Table 2, final score: SAGE is highest in all 20 settings, by +8.73 points on average over SkillOpt. The paired comparison alone gives +6.20 and the test adds +2.53. The split behind "final score" is not defined in the text.

**Stated limitations (§5.2–5.3).**
- Binary verifiers only; graded rewards would need e.g. a signed-rank test.
- The sign test ignores magnitude.
- The α guarantee is per comparison: "the validation set is reused across optimization steps", so trajectory-level error is uncontrolled.
- λ, τ, α need manual tuning.
- Text-only evaluation.
- Generation is fixed; co-design with the optimizer is future work.

**Related work (§2).** Self-Refine, Reflexion, STaR, OPRO, EvoPrompt, PromptBreeder, TextGrad, GEPA, DSPy, Voyager, ADAS, Trace2Skill and SkillOpt. **Not cited:** autoresearch / AI Scientist, sequential testing, multiple testing, reusable holdout / Ladder, Bayesian optimisation, R&S. Confidence sequences and empirical-Bernstein bounds appear only as future work. §2 claims the acceptance step "has not been explicitly studied under evaluation noise".

**What a reviewer will demand of us.** A paired one-sided test gate (SAGE / McNemar → paired t or sign test on seeds) as an E2 arm, at matched **run** budget. The incumbent re-evaluation SAGE gets for free on fixed items costs us runs.

**Overlap with Paper B.**
- **C1:** close in spirit. SAGE measures harm from naive acceptance as regression rate on already-solved items. It does not measure false keeps or discards against fresh-seed truth, and it does not measure wasted runs.
- **C2:** shares the motivation (optimizer's curse) and an incumbent-relative accept rule. It has **no prior, no Bayes threshold, no run price, no verify-vs-new-proposal trade-off, no skip rule and no formal winner's-curse result**.
- **C3, C4:** no overlap. Every candidate is executed, and the proposer is fixed.

**Differentiator we can defend.** "SAGE (Wang et al., 2026) replaces mean-improvement acceptance with a paired frequentist test per comparison, motivated informally by the optimizer's curse. We instead derive a Bayes acceptance threshold from a per-proposal prior and a run price. We prove that the record's upward bias holds for any adaptive proposer. We also decide, before execution, whether a proposal is worth a run at all."

**Relation to our pilot.**
- *Supports* C1/C2: naive keep-if-better causes large measurable harm. The gain comes from **raising the acceptance bar**, which is the same direction as our t* > 0 when μ < 0 (memory on: 24 % of informative proposals improve).
- *Not in conflict with* our verify finding (E1b: zero verify headroom; T2 Proposition 5). SAGE's incumbent re-scoring is a re-run on fixed items with no extra proposal cost. Under a run budget the same check costs 2r runs, which is the regime where T2 Proposition 5 says it rarely pays. Make this point explicitly in related work.

---

## 2. FOREAGENT: "Can We Predict Before Executing Machine Learning Agents?" (Zheng, Zhang, Luo, Mao, Gao, Du, Chen, Zhang; arXiv 2601.05930v2, ACL 2026 long 182)

**Setting (§2.1, §3.1).** The objective is arg max_C M(I, C, D) over full ML solutions C. The prediction task is **pairwise**. Given the task instruction I, a data-analysis report D_rep, two solutions {C0, C1} and a system prompt, the LLM outputs reasoning, a winner ŷ ∈ {0, 1} and a self-reported confidence c ∈ [0, 1] (§3.1).

**Corpus and labels (§3.2–3.3).**
- Trajectories of AIDE and AutoMind (DeepSeek-V3.1 and o3-mini) on MLE-bench: 1,329 valid solutions on 26 tasks, including "logically incomplete but executable intermediate states".
- Expert pruning (deduplication, taxonomy tagging, capping dominant methods) leaves 895 solutions. Exhaustive pairing gives **18,438 pairs**: CV 5,952; NLP 6,682; DS 5,804. The position of the true winner is balanced.
- Labels: "execution results". The paper **does not say whether the label is the hidden test score or the local validation score**. §5.4 implies the target is test performance.
- "Strict filtering to discard ambiguous pairs" is applied, but the criterion (margin, ties) is **not defined**. No seed or repeat-run model is given for the labels.

**Predictor (§3.4, §4).**
- **Prompting only: no fine-tuning, no trained predictor.**
- A "Verified Data Analysis Report" is produced as follows: GPT-5.1 writes profiling code with labels masked, the code runs in a sandbox, a human checks pass/fail, and GPT-5.1 verbalises the result.
- Accuracy (temperature 1.0, mean of 3 runs): DeepSeek-V3.2-Thinking **61.5 %**, GPT-5.1 **58.8 %**; random 50.0 %; complexity heuristic 50.8 % (§4.1–4.2, Table 2).
- Analysis (§5):
  - code only 56.7 %, numerical statistics 59.0 %, verbal report 61.3 %;
  - CoT 61.3 % vs direct 55.9 %;
  - Qwen 4B–1T 52.6–55.0 %, a "capacity ceiling" (Finding 4);
  - ranking 5 candidates: Acc@1 31.1 %, Spearman ≈ 0.22–0.25 (Table 3);
  - calibration: "self-reported confidence correlates with accuracy" (Fig. 3e, Finding 3), but no calibration metric is reported.
- **§5.4 "The Validation-Test Gap", Table 4:** execution-based M_val agrees with the label in only **72.2 %** of pairs, vs 61.5 % for the LLM and 50 % for random. The paper attributes the gap to distribution shift and validation overfitting, and calls 72.2 % an "Indirect Epistemic Bound" (Discussion 6.1).

**FOREAGENT loop (§6.2).**
- m = 10 candidates are proposed in parallel.
- A confidence gate (c = 0.7) is applied "to ensure high-certainty selection".
- The top-k (k = 1) candidate "is physically verified".
- So **9 of 10 candidates are skipped outright** without execution. This is implied, not stated explicitly. The text does not say how the 10 are reduced to 1 (tournament or vs incumbent), what happens below c = 0.7, or whether keeping requires the executed score to improve.

**Experiments (§6.3–6.4, App. C).**
- Baseline: AIDE under a 12 h limit, both using DeepSeek-V3.2 for coding, 3 independent runs.
- Results: ≈ 6× faster convergence, 3.2× more nodes explored, +6 % Beat Ratio (Table 13: 0.695 AIDE vs 0.739 FOREAGENT).
- AI4Science: 5 tasks (3 seen, 2 unseen), e.g. Aerial Cactus 0.698 → 0.877.
- App. C.6: k = 1 gives "Val Test Agreement" 75.23 % and Test Improve Rate 53.49 %, vs 30.39 % for AIDE (C.5). k = 2 raises the average node count to 157.87 (Table 15 not readable).

**Stated limitations.**
- The corpus is skewed to classification/regression, with long-tail domains under-represented.
- Reports for CV and NLP rely on metadata.
- "The current implementation has not yet been pushed to its optimal limit".

**What a reviewer will demand.**
1. A FOREAGENT-style pairwise LLM predictor (candidate config vs incumbent config, with confidence) used as a **screen**. This is close to A4, but A4 asks typed questions. Add the literal pairwise prompt as an A4 variant.
2. The generate-m-execute-1 regime as an alternative use of the LLM-call budget, i.e. a "best-of-m pre-selection" arm at the matched LLM-call cap.
3. An answer to why our 12-bin increment distribution is better than a pairwise win probability: the decision value needs μ, τ and π, not P(win) alone.

**Overlap with Paper B.**
- **C3 (strongest overlap):** an LLM predicts, before execution, which candidate is better, and the prediction is used to skip execution.
- **C1:** FOREAGENT's §5.4 shows execution noise empirically (validation agrees with test in 72 % of pairs). It never models it.
- **C2:** none. There is no threshold, no run price, no theory, and the 0.7 gate is ad hoc.
- **C4:** none.

**Differentiator we can defend.** "FOREAGENT (Zheng et al., 2026) prompts an LLM for pairwise preferences between complete solutions and executes the top-ranked one, with labels from single execution outcomes. We predict, for a bounded edit, the distribution of its increment over the incumbent: the inert mass π, the mean μ and the spread τ. Labels are fresh-seed audits, and we train the predictor (SFT on soft labels, then decision-focused GRPO). Its output feeds derived screening and acceptance rules whose value is bounded in advance (T4 Propositions 7–8). FOREAGENT neither trains the predictor nor models noise or the decision rule."

**Relation to our pilot.**
- *Supports* C1: the 72.2 % validation-test agreement is an outside measurement of how noisy single executions are as labels. It also motivates our audited labels: a predictor trained on raw outcomes is bounded by the label noise.
- *Supports* the premise of C3: pre-execution signal exists, but it is weak (61.5 %, and only 52–55 % for open Qwen models up to 1T). Small open models are near chance on *pairwise whole-solution* comparisons. That is a warning for A5 and H2. Our task is easier because the edits are bounded and the ledger is available, and the rule-detectable inert mass is 39–77 % repeats. Say so, and report A2 so that the learned gain is not credited for duplicate detection.

---

## 3. Beneath the Diff: "Diagnosing and Mitigating Algorithmic Mode Collapse in Code-Level Autonomous Research Loops" (He, Zhang, Jin, Liu; arXiv 2609.00077v1, 31 Aug 2026)

**Setting and loop (§3.1, §4.1).**
- Loop: the LLM proposer emits a description and a patch; the executor runs it; the edit is kept or reverted. Keep "typically when the metric improves by more than a noise threshold ϵ", formally R(m_opt(P⊕ρ) − m_opt(P)) = 1.
- B1 is "a faithful reimplementation of Karpathy (2026)" autoresearch.
- Tasks:
  - T1: GPT-2-small-style pretraining (≈ 124M parameters, 0.5B tokens; validation loss);
  - T2: Llama-3.2-1B LoRA on Alpaca (dev win-rate);
  - T3: Qwen-2.5-1.5B on GSM8K (dev accuracy);
  - T4: DSPy-style prompt program, Llama-3.2-3B (ARC-Easy dev).
- Proposers: Claude Opus 4.7 (main, temperature 0.7), GPT-5.2, Llama-3.3-70B. T = 300 iterations.

**Noise model (§3.3, §4.1.3).**
- Three metrics: m_opt (in-loop, drives the keep), m_audit (independent prompts and data partitions) and m_blind (read by no component, evaluated once per run; e.g. WikiText-103, SVAMP).
- 3 seeds (5 for T1) across runs.
- **No per-decision noise model. ϵ is never given a value or a selection rule.** No measurement of how often keeps are wrong.

**Collapse metrics (§3.2–3.3, §4.1.3).**
- Surface diversity S_t: normalised Levenshtein distance, window 20.
- Semantic clusters C_t: HDBSCAN cluster count.
- Mechanism entropy H_t over 9 categories (taxonomy κ = 0.84).
- Corpus similarity V_t (descriptive only).
- Cluster decay ΔC = (C_{T/5} − C_T)/C_{T/5}.
- Faithfulness gap Δ^faith_t = ḡ^opt_t − ḡ^audit_t (Eq. 1); ratios ρ^audit = ḡ^audit/ḡ^opt and ρ^blind = ḡ^blind/ḡ^opt, where values below 1 indicate Goodharting.

**DAPS (§3.4, Algorithm 1).**
- (i) Category-coverage reweighting: w(ρ) = exp(−log p_t(c(ρ))/τ_c), where p_t is the category frequency over the last W accepted edits.
- (ii) Persistent edit memory (PEM): a FIFO of Sentence-BERT embeddings of the last M = 200 **accepted** edit descriptions. A candidate with max cosine > τ_m = 0.85 is **dropped before execution**. **Rejected edits are not stored.**
- (iii) Validation gate (HVG): every K = 10 iterations, if Δ^faith_t > τ_h (task-calibrated, values not shown), revert to the last faithful checkpoint and append a failure summary to the history. It uses m_audit; fresh seeds are not stated.

**Results (§4.2–4.8).**
- Table 2, vanilla AR → DAPS: in-loop gain essentially equal (T1 +0.142 → +0.139; T2 +8.9 → +8.8; T3 +11.7 → +11.5; T4 +9.4 → +9.3). ρ_audit rises from 0.41/0.46/0.38/0.49 to 0.78/0.80/0.74/0.82.
- Table 11, ρ_blind: 0.39–0.46 → 0.69–0.78.
- Table 4, averaged over tasks: ΔC 0.68 → 0.21; H_T 1.18 → 1.71.
- App. D: by iteration 200 on T1, "74% of accepted edits modify the learning-rate schedule or AdamW hyperparameters".
- §4.3, matched audit access: HO-EarlyStop ρ_audit 0.62; HO-Revert 0.67; DAPS 0.79. "Audit access alone reaches at most ρ audit T = 0.67".
- §4.5, ablation: the components are sub-additive; HVG gives the largest single jump in ρ.
- §4.6: collapse appears under every proposer, worst for Llama-3.3-70B.
- §4.7: the same pattern with Aider.
- App. L: at T = 1000 the collapse deepens (ρ 0.31).
- §4.8: iterations to 80 % of terminal gain, 154 vs 163.
- **No counts of re-proposed, duplicate or no-op edits, and no acceptance rates.**

**Stated limitations.**
- Scale "confined to model and data scales accessible on a single A100 machine".
- m_audit is a validation signal: "can thus influence the trajectory".
- Corpus similarity is not evidence of retrieval.

*Reviewer-side observation (ours, not checked):* the stated design (T = 300 runs of 124M-parameter / 0.5B-token pretraining per loop, × seeds × ≈ 9 methods × 3 proposers) looks large for a single A100. Do not lean on its absolute numbers.

**What a reviewer will demand.**
1. DAPS (or its PEM component) as a proposer-side baseline. PEM is a **pre-execution skip rule by embedding similarity** and is the nearest heuristic to our A2.
2. HO-Revert as a periodic audit/verify baseline, closest to our verify action.
3. A discussion of in-loop vs audited gain: their ρ_audit ≈ 0.4–0.5 is the winner's curse of the in-loop record, measured.

**Overlap with Paper B.**
- **C1:** same loop family. They show the in-loop record overstates audited gain by roughly 2× (ρ ≈ 0.4–0.5), and they show repetitive edits. They do not separate noise-driven false keeps from Goodharting, and they do not count wasted runs.
- **C2:** none formally; ϵ is unspecified. ρ_audit < 1 is empirical support for T4 Proposition 9 (record bias), although their gap also contains genuine overfitting to m_opt's data, which our fresh-seed-same-data audit does not.
- **C3:** PEM skips without execution, but on diversity grounds and only against accepted edits. It has no value prediction and no run price.
- **C4:** the HVG appends failure summaries to the proposer's history, so the displayed memory changes. They do not test decision-dependence of proposals.

**Differentiator we can defend.** "Beneath the Diff (He et al., 2026) documents that keep-if-better research loops concentrate on a few edit mechanisms and that in-loop gains overstate audited gains. It mitigates both with proposer-side diversity heuristics and a periodic audit revert. We work on the control-plane side. We measure decision errors against fresh-seed truth, derive the Bayes acceptance and screening rules and the record's bias for any adaptive proposer, and learn the per-proposal prior those rules need. Their heuristic duplicate filter (PEM) is one of our baselines."

**Relation to our pilot.**
- *Supports* memory-driven concentration: 74 % of accepted edits target the LR schedule or AdamW, versus our 39–77 % repeats of evaluated configurations.
- *Supports* our verify skepticism indirectly: HVG is the costliest component (§4.5), and DAPS adds only ≈ 1.4 % wall-clock because audits are amortised every 10 iterations.
- *Note:* their PEM ignores rejected edits. The VbNA paper (§4 below) shows rejected edits are exactly what gets re-proposed. Our ledger-based features (config-hash seen-before, D27; last decision for the key) cover both.

---

## 4. Visible but Not Avoided: "State-Dependent Re-Proposal of Rejected Candidates in Catalog-Based LLM Optimization Loops" (Chen, Chen, Vong; arXiv 2610.15738v1, 11 Oct 2026)

*Read via the alphaXiv mirror because arXiv returned HTTP 429. Appendices F–I are missing.*

**Setting (§4.1).**
- A Qwen3-VL-8B screenshot GUI agent is evaluated on 60 development items from 9 synthetic apps (base accuracy 0.75).
- The proposer picks **one of 40 catalogued harness edits** (29 prompt, 9 rendering, 2 decoding). Keep if accuracy rises by more than δ = 0.02. 30 iterations per loop.
- Agent calls are **cached per harness**, so evaluation is deterministic given the harness; proposer temperature is 0.
- Proposers: Gemma-4-26B-A4B-it, Mistral-Small-3.2-24B-Instruct, Qwen3-VL-32B-Instruct, via OpenRouter.
- Design: 3 models × 2 catalogs (A: E01–E40; B: recoded and reworded) × 2 views × 3 seeds = 36 loops.
- History entry: edit, new accuracy, kept / not kept, and two failed items. The proposer sees the last 8 entries (W8) or the full history.

**Noise model.** Effectively **none**. Evaluation is cached and deterministic, and δ = 0.02 is a fixed margin. Seeds are proposer/run seeds. Their duplicates are therefore pure waste, while ours are noisy re-measurements: under T2 Proposition 5 they are worth little, but not zero.

**Definitions (§1, §3.1).** "A re-proposal is identified exactly by the edit's name" (§1). B_t = choosing an edit currently shown as rejected. D_t = choosing any harness–edit pair already evaluated. Invalid replies are excluded.

**Findings (§5).**
- **Probe vs loop (§5.1, Table 1).** In clean static probes the models almost never name a shown-rejected edit (0/60, 0/60 and 5/60). In their own loops they do. The loop-minus-probe macro difference is **0.32 [0.27, 0.37]**, positive in all 6 cells. "Low re-proposal in a static probe does not guarantee low re-proposal in the states an optimizer reaches" (§1).
- **Waste.** Duplicate harness–edit pairs take **32 % (103/324), 28 % (98/350) and 63 % (226/357)** of valid iterations.
- **State dependence (§3.3, §5.1).**
  - Without history, rejected edits stay attractive (enrichment log-odds +2.72, +1.28, +2.11).
  - They show no excess over the proposer's other earlier choices (e.g. Gemma-4 +0.07 [−1.31, 1.61]). The authors read this as **self-selection**: loop-rejected edits are the proposer's own preferred choices. They do not claim it is a proven mechanism.
  - Same-harness reconstruction gives M − A = −0.04 (90 % CI [−0.07, −0.01]).
- **History is model-specific.** It lowers re-proposal for Gemma-4 (−0.57) and Qwen3-VL-32B (−0.36) and raises it for Mistral (+0.31 [0.12, 0.49]).
- **Failure evidence (§4.3, §5.2, Table 2).**
  - Deleting the failed items lowers re-proposal (−0.19 [−0.25, −0.13]).
  - A neutral length-matched replacement gives −0.07 [−0.13, −0.01] (Holm p 0.071). The effect is model-specific.
  - "Failure-target attraction" is the most frequent stated reason (κ = 0.62).
- **Rejection signal (§4.4, §5.3).**
  - A neutral ID list: −0.06 [−0.13, 0.00].
  - **One status sentence: 0.30 → 0.09.** F − N = −0.16 [−0.22, −0.09] (log OR −1.44), negative in every model.
  - Adding a prohibition: a further −0.05 (Holm p 0.054, not supported).
  - The original "DO-NOT" sentence: −0.27 on fresh states.
- **Boundary (§5.4, App. E).** A thinking variant re-proposes far less than instruct (18/40 vs 2/40; −0.40 [−0.55, −0.25]).

**Stated limitations.**
- One synthetic GUI agent and one 40-edit catalog.
- Free-text optimizers are not studied.
- The framework was developed after the first experiments.
- Several contrasts are post hoc.
- The ±0.10 equivalence margin is not separately justified.
- Only three open models; provider routing was not pinned for the main interventions.
- LLM-only annotation.

**Related work (§2).** OPRO, GEPA, DSPy (archives with no enforced avoidance); tabu search (Glover 1986); novelty archives (Lehman & Stanley 2011); negation weaknesses (Castricato et al. 2024); Gumaan (2026) (a failure record raises repetition, and "do not repeat" has no effect there); Yang (2026); Shi et al. (2023).

**What a reviewer will demand.**
1. A **hard tabu / exact-duplicate filter** as a baseline. It is our A2 (D27 config-hash flag), so state it as a classical tabu rule.
2. A **"rejection-status sentence" memory variant** beside our debiased-memory variant in C4. Otherwise a reviewer can say the display effect is generic salience, not debiasing.

**Overlap with Paper B.**
- **C1:** independent replication of the waste magnitude (28–63 % duplicate pairs vs our 39–77 % repeats).
- **C4:** **closest prior for the proposer-feedback channel.** They show that what the history displays about decisions changes the next proposals in a model-specific way, which is a direct DI-relevant manipulation.
- **C2, C3:** none. They have no noise, no acceptance theory and no predictor; avoidance is left to the proposer or the prompt.

**Differentiator we can defend.** "Chen et al. (2026) show, in a deterministic catalog setting, that LLM proposers re-propose their own rejected candidates in trajectory-dependent ways and that how rejection is displayed changes this. We formalise the consequence for control. When the proposal law depends on keep/discard decisions, myopic acceptance can be arbitrarily suboptimal (T4 Proposition 10). We test that dependence with matched-history forced-decision branches under a noisy metric. We also screen the resulting duplicates before execution instead of relying on the proposer to avoid them."

**Relation to our pilot.**
- *Supports* our DI-test direction. The memory-on partial arm's value residual is −0.00122 [−0.00222, −0.00026] ("violated in value terms", PILOT, PARTIAL); memory off is undetermined. VbNA's history manipulations change proposals with model-specific sign, which is consistent with DI failing for memory-reading proposers and possibly holding for others.
- *Caution for C4.* Their effect is driven by self-selection (rejected edits are ones the model already prefers), not only by memory content. For us this means the C3 prior should use the proposer's own history (last decision for this key; times this key edited), and the DI effect may be smaller than "memory feedback" suggests. Our next-k absolute-metric DI test measures the net effect, which is the right estimand.
- *Supports* putting duplicate screening in the control plane (A2/A3) rather than the prompt. Even the best display intervention leaves re-proposal at 0.09, and the sign of the history effect varies by model.

---

## 5. Classical references: exact statements we would cite

| Reference | Verified statement (source) | Use in Paper B |
|---|---|---|
| Smith & Winkler 2006, *Management Science* 52(3):311–322, doi 10.1287/mnsc.1050.0451 | "we should expect the value of the chosen alternative to be less than its estimate, even if the value estimates are unbiased"; the cause is "the optimization-based selection process"; remedy: "Bayesian methods to adjust value estimates", "disciplined skepticism" (abstract, RePEc). *Note:* the abstract does not use the words "biased upward". | Motivation for the record's bias (C2-iv); T4 Proposition 9 extends it to an adaptive proposer and a frozen running record. |
| Chick & Frazier 2012, *Management Science* 58(3):550–569, doi 10.1287/mnsc.1110.1425 | "The optimal procedure is derived for comparing a known standard with one alternative"; it "accounts for the expected benefit of adaptive stopping policies"; it uses "dynamic programming to model sequential sampling as an option to learn" (abstract, RePEc). The abstract does not mention sampling cost explicitly; check the body before claiming it. | Verify VoI vs run price (C2-ii) is an instance of one-alternative-vs-standard with sampling economics. Our addition is that the "standard" is a noisy frozen record and that the price of a sample is a forgone new proposal. |
| Xie & Frazier 2013, *Operations Research* 61(5):1174–1189, doi 10.1287/opre.2013.1207 | Identify systems with mean above a known threshold. The Bayes-optimal fully sequential policy is "the solution to a dynamic program", which "can be solved efficiently" under probabilistic termination or sampling costs, using optimal stopping and bandit techniques (abstract, RePEc). | The Bayes keep threshold (C2-i) is a one-shot instance of comparison with a known standard. Our setting differs: the standard is the incumbent's recorded noisy value and alternatives arrive from an adaptive proposer. |
| Blum & Hardt 2015, ICML (PMLR 37), arXiv 1502.04585 | Algorithm 1 (§3): release R_t ← [R_S(f_t)]_η only "if R_S(f_t) < R_{t−1} − η", else keep the previous best. Definition 2.1: leaderboard error = max_t \|min_{i≤t} R_D(f_i) − R_t\|. Theorem 3.1: for η = O(n^{−1/3} log^{1/3}(kn)), the error is O(log^{1/3}(kn)/n^{1/3}) w.h.p. under fully adaptive submissions. | A Ladder-style margin rule is a reference E2 arm (keep iff Δ̂ > η). It is the frequentist, worst-case analogue of our Bayes threshold and also controls the record's bias under adaptivity. Cite as the closest classical antecedent of C2-iv. |

---

## 6. Comparison table

| | SAGE | FOREAGENT | Beneath the Diff | VbNA | **Paper B** |
|---|---|---|---|---|---|
| Object edited | skill text | whole ML solution | training-pipeline code | 1 of 40 catalog edits | bounded edit to ML training script |
| Noise model | implicit (finite items); none measured | none (§5.4 gap only) | none; ϵ unspecified | none (cached, deterministic) | σ per node/edit kind, fresh joint seeds |
| Seeds reported | no | 3 runs | 3 (T1: 5) | 3 proposer seeds | per-instance seeds; K = 6 audit seeds |
| Acceptance | paired one-sided binomial test + regression cap | top-1 executed; keep rule unstated | improve > ϵ; HVG revert every 10 | improve > 0.02 | Bayes t* = −μσ²/τ² per proposal |
| Pre-execution skip | no | yes (9/10, pairwise LLM, c = 0.7) | yes (PEM, cosine > 0.85 to accepted) | no | yes, (1−π)V ≥ g |
| Predictor trained | — | no (prompting) | — | — | yes: LightGBM, SFT on soft audited labels, decision-focused GRPO |
| Run price / budget theory | no | no | no | no | yes (g; T2 Prop. 5, T4 Prop. 8) |
| Winner's curse | informal citation | empirical (72.2 %) | empirical (ρ_audit ≈ 0.4–0.5) | — | Prop. 9, any adaptive proposer |
| Proposer feedback | fixed generator | — | diversity heuristics | measured (history, status display) | DI condition (Prop. 10) + forced-decision test + debiased display |
| Waste measured | no | no | no (74 % concentration) | 28–63 % duplicate pairs | 39–77 % repeats; 9–14 % identical to incumbent |

**Novelty verdict (full text).** None of the four combines a noise model, incumbent-relative acceptance and a learned per-proposal prior or pre-execution screen. No paper contains a formal result corresponding to T4 Propositions 7–10. No paper trains a predictor of the edit's increment, and none uses decision-regret post-training. The abstract-level conclusion of 18 Oct holds after the full read.

Two points need sharper wording, because they are the claims most exposed to these papers:
- (a) "pre-execution screening" is not new in itself (FOREAGENT, DAPS-PEM). Novelty lies in a *value-based screen under a run price with a learned increment distribution*.
- (b) "LLM proposers repeat rejected candidates" is now published (VbNA). Our C4 novelty lies in the *decision-dependence condition and its test under noise*, not in the observation of repetition.

---

## 7. Baselines we must implement, and how

1. **SAGE gate (E2 arm).** At each executed proposal, run candidate and incumbent on r common fresh seeds (the paired design), and form per-seed differences d_j. Keep iff mean d > 0, a one-sided sign / binomial test (or paired t, since our metric is continuous; SAGE §5.3 names signed-rank for graded rewards) has p < α, and the worst per-seed regression is within the cap. Charge 2r runs per decision at the matched run budget. Tune α on dev instances. Report it beside A1 and PACE: under T2 Proposition 5 we expect it to lose at matched W because of run cost. That is a C2 prediction, and SAGE gives it a citable foil.
2. **FOREAGENT-style pairwise screen (A4 variant, "A4-pair").**
   - Prompt the manager LLM (and, separately, the A5 base model zero-shot) with the incumbent config, the candidate edit and the ledger summary. Ask "which configuration will score higher on validation?" plus a confidence in [0, 1], with CoT, which mattered in their §5.2.
   - Map to P(Δ > 0) with an isotonic map on dev. Screen: execute iff P(Δ > 0) ≥ c, with c tuned on dev (their value is 0.7).
   - Second mode, "best-of-m": generate m proposals per step (m = 4 to stay within the LLM-call cap), execute only the top-1 by pairwise tournament vs the incumbent, then keep under the default rule. This is the literal predict-then-verify loop, at the matched LLM-call cap.
3. **DAPS-PEM duplicate filter (proposer-side appendix arm).** Embed edit descriptions (Sentence-BERT) and drop a candidate whose cosine to any of the last M accepted edits exceeds 0.85. Variant: include rejected edits too, which is what VbNA suggests. Compare with A2 (exact config hash + inactive key) to show which waste is rule-detectable.
4. **HO-Revert / periodic audit (verify reference).** Every K = 10 runs, audit the incumbent on fresh seeds and revert if the audited gain is below a fraction of the recorded gain. This is the closest published analogue of our verify action. Charge its runs.
5. **Ladder margin rule (E2 arm).** Keep iff Δ̂ > η, with η tuned on dev or set to c·σ_node. This is the frequentist adaptive-holdout analogue of t*.
6. **Rejection-status display (C4 control).** Add one sentence to the memory summary, e.g. "Edits marked discard were tested and did not improve; proposing them again wastes a run", the VbNA §4.4 "F" condition. Compare against the debiased B̃ display and the plain display, so that the C4 effect is not just salience.

---

## 8. Proposed edits to C3_DESIGN §10 and related work (text only; C3_DESIGN.md not edited)

**Replace the first paragraph of §10 with:**

> **Full-text read, 19 Oct 2026 (`inputs/NOVELTY_FULLTEXT_20261019.md`).** No work combines an LLM proposer, a noise-modelled incumbent-relative acceptance rule, and a learned per-proposal prior used for pre-execution screening. Four 2026 papers each cover part of this, and reviewers will know them:
> - **SAGE** (arXiv 2609.36043) gates skill-document edits with a paired one-sided binomial test plus a regression cap. It cites the optimizer's curse informally and offers no theorem. It has no prior, no run price, no screening, a fixed generator, and no seeds or noise measurement.
> - **FOREAGENT** (ACL 2026) prompts, without training, an LLM for pairwise preferences between whole ML solutions (61.5 % for DeepSeek-V3.2, 52–55 % for open Qwen). It executes the top-1 of 10 candidates behind a 0.7 confidence gate. Its labels come from single executions with an undefined ambiguity filter. Validation agrees with test in only 72.2 % of pairs (§5.4).
> - **Beneath the Diff** (arXiv 2609.00077) studies the same keep-if-better ML-edit loop. In-loop gains overstate audited gains (ρ_audit 0.38–0.49) and accepted edits concentrate on a few mechanisms. Its DAPS includes an embedding-similarity pre-execution filter (against accepted edits only) and a periodic audit revert. The keep margin ϵ is unspecified.
> - **Visible but Not Avoided** (arXiv 2610.15738) shows, in a deterministic 40-edit catalog loop, that proposers re-propose their own rejected edits. Duplicates take 28–63 % of iterations, and the effect of history is model-specific; a one-sentence rejection-status display cuts re-proposal by 0.16.

**In §10 item 2 (C3 differentiators), add:**

> - Pre-execution skipping exists (FOREAGENT top-1-of-10; DAPS-PEM similarity filter). Our screen is **value-based**: (1 − π)V(t*; μ, τ, σ) ≥ g, with a run price and an a-priori bound on its gain (Propositions 7–8). It is driven by a **trained** increment-distribution predictor, not a prompted pairwise preference or a diversity heuristic.
> - FOREAGENT's own §5.4 (72.2 % validation-test agreement) motivates audited labels: a predictor trained on single noisy outcomes is capped by label noise.

**In §10 item 3 (reference arms), replace with the six arms of §7 of the input file:**

> SAGE paired-test gate; FOREAGENT pairwise screen (threshold mode and best-of-m mode at the matched LLM-call cap); DAPS-PEM filter, with an accepted+rejected variant (appendix); HO-Revert periodic audit; Ladder margin; and, for C4, a rejection-status display control.

**Replace §10 item 4 with:**

> Read in full on 19 Oct (VbNA via the alphaXiv mirror; arXiv 429). Verify quotes against the PDFs before submission.

**§8 risk table, new row:**

> | Small LMs near chance on pairwise prediction (FOREAGENT: Qwen 52–55 %) | A5 ≈ A2/A3 | Our target is a bounded edit plus ledger, not a whole-solution comparison; report A2 so the inert mass is not credited to learning; H2b (transfer) carries the LM claim |

**Related-work paragraph (draft for the manuscript):**

> *Acceptance under noise in agent loops.* SAGE (Wang et al., 2026) replaces mean-improvement acceptance of skill edits with a paired one-sided test and a regression cap, motivated by the optimizer's curse (Smith & Winkler, 2006). Its error control is per comparison, and it notes that trajectory-level error is uncontrolled because the validation set is reused. The Ladder (Blum & Hardt, 2015) bounds leaderboard error under adaptive submissions by accepting only improvements larger than a margin. We derive instead a Bayes acceptance threshold from a per-proposal prior, in the tradition of comparisons with a known standard (Chick & Frazier, 2012; Xie & Frazier, 2013). We show that the recorded incumbent value is biased upward for any adaptive proposer, and that re-measurement competes with new proposals for one run budget.
>
> *Predicting before executing.* FOREAGENT (Zheng et al., 2026) prompts LLMs for pairwise preferences between ML solutions and executes only the preferred candidate. It reports 61.5 % pairwise accuracy and notes that local validation agrees with test outcomes in only 72 % of pairs. Beneath the Diff (He et al., 2026) filters candidates similar to past accepted edits. Our predictor is trained on fresh-seed-audited increments, outputs the distribution (π, μ, τ) that the derived screening and acceptance rules consume, and is post-trained on the regret of those rules.
>
> *Proposer feedback.* Code-level research loops concentrate on few edit mechanisms, and their in-loop gains overstate held-out gains (He et al., 2026). LLM proposers re-propose their own rejected candidates in state-dependent, model-specific ways (Chen et al., 2026), consistent with tabu-style exclusion being left to the proposer. We give the condition under which per-proposal (myopic) control is optimal despite such feedback, and we test it with forced-decision branches under a noisy metric.
