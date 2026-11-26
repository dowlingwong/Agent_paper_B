# Paper B pivot: prior-work novelty sweep and venue check

Date: 2026-10-09. Scope: the planned pivot of Paper B. In it, each loop of the governed autoresearch harness (LLM manager proposes a bounded edit, the worker trains, the control plane decides keep or discard, and every trial goes to the ledger) is treated as a DAC/RL decision problem. A small post-trained "configurator" decides **when and how** to intervene. Training and evaluation use paired counterfactual branches from restored checkpoints, with the replay-identification conditions from companion Paper A.

Contributions scored throughout:
- **C1**: a loop-level DAC/RL formulation of autoresearch control.
- **C2**: a "how to intervene" action space beyond *when*. The actions are reject/revise before running, verify by re-seed before keep, rollback to best, change step size or edit scope, change memory mode, early-stop a run, and stop the campaign.
- **C3**: a post-trained small configurator, compared against LLM self-control and against an LLM+configurator hybrid.
- **C4**: counterfactual-branch training and evaluation with replay-identification guarantees (bounded discrepancy p; thresholds 2p and p/(1−p)).

Method: WebSearch and WebFetch, run on 2026-10-09. I fetched each arXiv abstract page to confirm the title, authors and date. For a small number of papers I also read the HTML full text, and those entries say so. "Listing only" means the work appeared in search results with a real URL, but I did not open its own page. Entries already analysed in `B_NOVELTY_MEMO.md` are not redone. They are only re-scored against the new framing (§3).

Access failures, where the work continued without the page:
- arXiv HTML for 2608.21027 (COTA) returned HTTP 429. I read the alphaXiv abstract page for it instead.
- aaai.org `/aaai-27/workshop-program/` returned HTTP 429. I used the AAAI-27 workshops-call page instead.
- ebooks.iospress.nl (Biedenkapp et al., ECAI 2020) and 2027.automl.cc block fetchers through robots.txt.
- preprints.org 202608.2057 was not re-checked. The author has already excluded it.

---

## 1. Closest works (deep entries)

Overlap is rated as H (high), M (medium) or L (low) against each of C1–C4.

### 1.1 Ferreira, Wobbe, Krishnakumar, Hutter, Zela, *Can LLMs Beat Classical Hyperparameter Optimization Algorithms? A Study on autoresearch*, arXiv 2603.24647 (v5, 2026-04-17). https://arxiv.org/abs/2603.24647 (abstract and HTML v5 read)
- **What it does:** compares CMA-ES and TPE with LLM agents on Karpathy's autoresearch testbed, both in a fixed search space and with unconstrained code edits.
- **Centaur:** shares CMA-ES state (mean, step size, covariance) with an LLM. At each trial the LLM proposes with a fixed probability r = 0.3, ablated over 0.1–0.8; this rate is not learned. Centaur with a 0.8B LLM beats every classical and pure-LLM method.
- **Finding:** pure LLM agents "struggle to track optimization state across trials".
- **Noise handling:** across optimizer seeds only (3 seeds). There is no per-configuration re-evaluation. OOM trials are assigned val_bpb = 100.
- **Nothing is trained.**
- **Overlap:** C1 M (same testbed, same keep-best loop), C2 L–M (CMA-ES step size is the only "how" knob), C3 **M–H** (an LLM + classical-controller hybrid with a 0.8B model on autoresearch already exists), C4 L.
- **Differentiator B must claim:** B *learns* the arbitration that Centaur fixes at r = 0.3. B's actions act on the noisy keep/discard decision itself (verify, rollback, reject-before-run), not on who proposes. Centaur, CMA-ES and TPE must be arms on the same budget.

### 1.2 Yi & Song, *Learning to Control LLM Agent Harnesses with Offline Reinforcement Learning*, arXiv 2607.05458 (2026-07-05). https://arxiv.org/abs/2607.05458 (HTML v1 read)
- **What it does:** defines a finite-horizon "Harness MDP". A controller (a one-hidden-layer MLP with 64 units) picks one of seven structural actions (observe, retrieve, call-tool, draft, check, revise, submit) while the LLM stays frozen.
- **Training:** AWR on offline rollouts from base and exploratory harnesses, using terminal rubric rewards only.
- **Evaluation:** six domains (knowledge-work, coding, research QA, multi-tool, long-memory, planning) plus τ-bench retail and DB-Bench adapters. None of these is ML experimentation.
- **Baselines:** BC and Forced CHECK. There is **no LLM-self-control arm** and **no same-state branching**.
- **Overlap:** C1 **H structurally** (MDP over the harness, light controller, frozen LLM; only the domain differs), C2 M (check ≈ verify, revise, submit ≈ stop; no rollback, step size, memory mode or early-stop), C3 M, C4 L.
- **Differentiator:**
  - Domain: an ML-experiment loop with noisy, expensive, irreversible-cost actions and a keep/discard incumbent.
  - The LLM-self vs configurator vs hybrid comparison, which this paper lacks.
  - Paired-branch labels with an identification condition, against their logged offline buffers.
  - B cannot claim "harness control as an MDP with a light learned controller" as new.

### 1.3 Yu, Bai, Sun, et al., *PrimeScientist: Strategic Allocation of Research Effort in Autonomous Research*, arXiv 2609.17846 (2026-09-15). https://arxiv.org/abs/2609.17846 (HTML v1 read)
- **What it does:** frames research-effort allocation as a sequential decision problem. The state is task, plan set, history and remaining budget. The actions are expand a plan (up to 3 children), execute an untested plan, and stop at budget.
- **Policy:** a **hand-designed** MCTS-style rule with budget-dependent exponent α_t = min(1/r_t, α_max) and δ-pruning. There is no training. Both executor and reflector are GPT-5 or GPT-5-mini.
- **Results:** beats AutoResearch (a linear edit-run-keep/revert loop) on FIRE-Bench, AutoLab and 4 MLE-bench tasks.
- **Noise:** on FIRE-Bench each node is "executed twice and the higher score is recorded". This max-of-two rule is optimistic under seed noise, which is exactly the failure that a B verify action targets.
- **Overlap:** C1 **M–H** (autoresearch as budgeted sequential decision is already published), C2 L–M, C3 L, C4 L.
- **Differentiator:** a learned policy instead of a fixed MCTS rule. Interventions act on noisy accept decisions (verify, rollback) rather than on tree expansion. A noise-aware outcome makes max-of-two selection a named failure case. PrimeScientist-style allocation should be included as a comparator.

### 1.4 Shawn, *PACE: Anytime-Valid Acceptance Tests for Self-Evolving Agents*, arXiv 2606.08106 (2026-06-06). https://arxiv.org/abs/2606.08106
- **What it does:** treats "keep if it went up" against a noisy held-out estimate as uncontrolled adaptive multiple testing. It replaces that rule with a training-free, paired, testing-by-betting e-process commit gate. The gate bounds false-commit probability under optional stopping and decides how many evaluations to spend per candidate.
- **Evaluation:** Qwen2.5 0.5B–3B agents self-evolving prompts.
- **Overlap:** C1 L–M, C2 **M** ("verify before keep" with a principled sequential stopping rule is already published), C3 L (no learning, but it is the strongest non-learned verify baseline), C4 L.
- **Differentiator:** B's verify action is one of several, and is traded off against rollback, early-stop and campaign-stop under a shared budget. PACE (or an e-value gate) must be the "classical verify" arm. Without it, any gain from the configurator's verify action is unattributed.

### 1.5 Ji & Ding, *Rehearse: Stepping Back from the Confidence Cliff in Self-Improving Autoresearch*, arXiv 2607.27687 (2026-07-30). https://arxiv.org/abs/2607.27687
- **Finding:** the reliability of an LLM judge on *pre-execution* decisions in autoresearch falls late in the loop (selective accuracy 82.8% → 56.9%), and the judge keeps deciding. This is the "confidence cliff".
- **Fix:** a prompted skill that compares several ideas before running one and judges them with a focused outcome memory.
- **Evaluation:** 4,000 budgeted training runs across nanochat, image classification and time-series forecasting. No learned controller.
- **Overlap:** C1 L, C2 **M** (reject/compare before run, plus a memory intervention), C3 M (direct evidence that LLM self-control degrades over a campaign; it supports B's motivation but also pre-empts "LLM self-control is unreliable" as a finding), C4 L.
- **Differentiator:** a learned, state-dependent decision about *whether* to intervene and with which action, against Rehearse as a prompted, always-on remedy. Cite it as motivation. If cheap, include it as an LLM-side arm.

### 1.6 Jiang, Li, Wang, Zhai, Zhang, *Don't Solve, Just Compare: Tiny Advisors for Runtime Intervention in LLM Agents* (COTA), arXiv 2608.21027 (2026-08-21). https://arxiv.org/abs/2608.21027 (abstract via arXiv; details via https://www.alphaxiv.org/abs/2608.21027v1)
- **What it does:** a 0.5B comparator is trained on pairwise labels from **same-prefix counterfactual branches**: restore the prefix, change one action, keep the frozen actor.
- **Intervention rule:** repeated "candidate-relative domination" decides when to intervene, and the advice is non-binding.
- **Baselines:** Self-Reflection, AgentPRM, Asym-AC. Benchmarks: WebShop, ALFWorld, τ³-Retail.
- **Not stated:** how the prefix is restored.
- **Overlap:** C1 L–M, C2 L (advice only), C3 **M–H** (a tiny trained advisor beating the actor's own self-reflection), C4 **M–H** (same-prefix branch supervision for intervention).
- **Differentiator:** an explicit identification condition for branch labels where re-execution is *inherently* stochastic (GPU training). A typed multi-action intervention space instead of advice. A noisy-metric ML-experiment domain.

### 1.7 Xiao, Wang, Chen, et al., *When Harnesses Lose the Signal: Causal Evaluation of Recovery in LLM Agents* (CIR), arXiv 2610.00372 (2026-09-30). https://arxiv.org/abs/2610.00372 (HTML v1 read)
- **What it does:** forks with and without recovery from the same state (greedy decoding; it checks that histories are identical and reports "no environment-replay mismatches") and counts rescues and harms.
- **CIR router:** logistic-regression T-learner, with thresholds chosen to maximise net gain under a clean-harm limit ε. The action is binary (refresh or continue) and is applied at most once.
- **No formal identification assumptions.** It explicitly notes that marginal success probabilities do not identify joint rescue/harm.
- **No LLM-self-decided baseline.**
- **Overlap:** C1 L, C2 L, C3 L–M, C4 **M–H** (paired forks for intervention-policy learning with a harm constraint).
- **Differentiator:** replay discrepancy p enters the estimand and the decision rule, where CIR assumes mismatches are zero. Multi-action intervention. ML-training loop.

### 1.8 Calibration Is Not Control (Zhang et al., arXiv 2606.21399), re-scored for the new framing
The memo's analysis stands; see `B_NOVELTY_MEMO.md` §1.
- **What it does:** a three-action branch tree (continue, intervene, quit) from selected prefixes, mismatch-discarding replay, an RF witness with an LCB, and a realized-branch oracle.
- **Overlap:** C1 L–M, C2 M (it already has a "how" choice among three actions, including quit), C3 M (a small learned witness), C4 **H** on branching and **L** on the identification guarantee.
- **Differentiator:** unchanged from the memo. The only new element is the domain (autoresearch).

---

## 2. Further relevant works (short entries)

Overlap ratings are given in the order C1 / C2 / C3 / C4.

### 2a. DAC and LLM-as-configurator
| Work | Verified | Summary | Overlap |
|---|---|---|---|
| Biedenkapp et al., "Dynamic Algorithm Configuration: Foundation of a New Meta-Algorithmic Framework", ECAI 2020 | Listing only. iospress blocks fetchers; listing at https://astro.paperswithcode.com/paper/dynamic-algorithm-configuration-foundation-of; PDF https://ebooks.iospress.nl/pdf/doi/10.3233/FAIA200122 | Defines DAC as a contextual MDP over per-step parameter settings. | M / L / L / L |
| Adriaensen, Biedenkapp, Shala, Awad, Eimer, Lindauer, Hutter, "Automated Dynamic Algorithm Configuration", arXiv 2205.13881 | https://arxiv.org/abs/2205.13881 (the arXiv page names no venue; the JAIR 2022 venue comes from the task brief and was not checked) | DAC formalisation and survey across EA, planning and ML. | M (vocabulary) / L / L / L |
| Eimer et al., "DACBench", IJCAI 2021 | https://www.ijcai.org/proceedings/2021/230 | Benchmark library for DAC. | L / L / L / L |
| Nguyen, Le, Biedenkapp, Doerr, Dang, "Deep RL for DAC: OneMax (1+(λ,λ))-GA", arXiv 2512.03805 | https://arxiv.org/abs/2512.03805 | DDQN and PPO for population-size control. Reports instability with long horizons and exploration. Evidence that RL-DAC is hard even on toy problems. | L / L / L / L |
| Lu et al., "Sequential Multi-Agent DAC", arXiv 2510.23535 | https://arxiv.org/abs/2510.23535 | MARL DAC with hyperparameter dependencies. | L / L / L / L |
| Taparia, Sagar, Senanayake, "Learning to Configure Agentic AI Systems" (ARC), arXiv 2602.11574 | https://arxiv.org/abs/2602.11574 | An SMDP with a lightweight hierarchical learned policy that picks a per-query agent configuration (workflow, tools, budget, prompts). | M / L / M / L |
| Xu et al., "AutoEP: LLMs-Driven Automation of Hyperparameter Evolution for Metaheuristic Algorithms", ICLR 2026 | https://iclr.cc/virtual/2026/poster/10008027 | A zero-shot LLM acts as an online algorithm controller using real-time landscape analysis, with no training. This is "LLM as DAC policy". | M / L / M (an LLM-only arm exists) / L |
| Fang et al., "LLMZero: adaptive training strategies for RL post-training via LLM agents", arXiv 2606.18388 | https://arxiv.org/abs/2606.18388 | An LLM agent diagnoses each checkpoint of a GRPO run and proposes multi-parameter transitions, with tree search over training trajectories. No trained controller. | M / M / L / L–M |
| Rao & Advani, "AI Training Manager: Bounded Closed-Loop Control of Adaptive Training Recipes", arXiv 2606.29871 | https://arxiv.org/abs/2606.29871 | An LLM monitors live training telemetry and applies interventions through a bounded, deterministically verified action interface. Not trained. Failures are induced. | L–M / M / L–M / L |
| Chacón Sartori & Blum, "irace-evo", arXiv 2511.14794 | https://arxiv.org/abs/2511.14794 | Static configuration (irace) joined with LLM code evolution. | L / L / L / L |

### 2b. HPO and multi-fidelity controllers (the "it's just HPO scheduling" axis)
| Work | Verified | What it controls | Overlap |
|---|---|---|---|
| Hyperband, Li et al., arXiv 1603.06560 | https://arxiv.org/abs/1603.06560 | Adaptive resource allocation with early stopping. | L / M (early-stop) / L / L |
| ASHA, Li et al., arXiv 1810.05934 | https://arxiv.org/abs/1810.05934 | Asynchronous successive halving with aggressive early stopping. | L / M / L / L |
| BOHB, Falkner, Klein, Hutter, arXiv 1807.01774 | https://arxiv.org/abs/1807.01774 | BO combined with Hyperband. | L / M / L / L |
| Freeze-Thaw BO, Swersky, Snoek, Adams, arXiv 1406.3896 | https://arxiv.org/abs/1406.3896 | Uses partial curves to decide halt / resume / new run. | L–M / M (pause/resume ≈ early-stop/rollback) / L / L |
| ifBO (FT-PFN), Rakotoarison et al., arXiv 2404.16795 | https://arxiv.org/abs/2404.16795 | In-context learning-curve surrogate that picks which configuration to continue. | L–M / M / L / L |
| PBT, Jaderberg et al., arXiv 1711.09846 | https://arxiv.org/abs/1711.09846 | Population-based schedule of weights and hyperparameters. Its exploit/explore copying is known from the paper body; the abstract page did not confirm it. | L–M / M (rollback-to-better + perturb) / L / L |
| Hyp-RL, Jomaa et al., arXiv 1906.11527 | Listing only: https://arxiv.org/abs/1906.11527v1 | HPO as an MDP with an RL policy over configurations. | M / L / L / L |
| AgentHPO, Liu, Gao, Li, CPAL 2025 (PMLR v280) | https://proceedings.mlr.press/v280/liu25c.html | An LLM agent runs the propose-run-learn HPO loop. | L–M / L / L / L |
| LLAMBO, Liu, Astorga, Seedat, van der Schaar, arXiv 2402.03921 | https://arxiv.org/abs/2402.03921 | LLM components inside BO. | L / L / L / L |
| Zhang et al., "Using LLMs for HPO", arXiv 2312.04528 | https://arxiv.org/abs/2312.04528 | Iterative LLM proposals; code as a hyperparameter. | L / L / L / L |
| Li, "Greedy Is a Strong Default: Agents as Iterative Optimizers", arXiv 2603.27415 | https://arxiv.org/abs/2603.27415 | An LLM replaces the proposal step of HC/SA; the acceptance rule stays classical. Greedy hill-climbing with early stopping is a strong default. | L–M / L–M / L / L |
| Guo et al., "ASAP", arXiv 2606.25207 | https://arxiv.org/abs/2606.25207 | An LLM picks among an optimizer pool per round, plus wall-clock system co-design. | L–M / L / L–M / L |
| Chen et al., "Efficient HPO for LLM RL" (JF-HPO), ACL 2026 | https://aclanthology.org/2026.acl-long.1271/ | Joint fidelity across model size and budget, with progress-based early stopping and checkpoint reuse. | L / M / L / L |
| Bouthillier et al., "Accounting for Variance in ML Benchmarks", arXiv 2103.03098 | https://arxiv.org/abs/2103.03098 | Seed and data variance can flip comparisons; motivates verify-by-reseed. | — (motivation) |

**Assessment of the HPO risk.** Each *timing* action in B has a classical analog:
- early-stop → Hyperband / ASHA / freeze-thaw
- verify by re-running before keep → racing and intensification (irace, SMAC), and PACE
- rollback-to-best and perturb → PBT exploit/explore
- step size → CMA-ES σ adaptation (Centaur)

What has no HPO analog is any action conditioned on the **content of a code-edit proposal**:
- reject or revise a diff before running it
- change the edit scope
- change the manager's memory mode

So does a governed control plane over an *LLM proposer*. That is the territory B must defend empirically (§4, R1).

### 2c. ML-engineering, AI-scientist and autoresearch agents
| Work | Verified | Summary of its controller | Overlap |
|---|---|---|---|
| Karpathy, autoresearch repo | https://github.com/karpathy/autoresearch | Agent edits `train.py`, 5-minute runs, val_bpb, keep or discard; no stopping or verification logic. | baseline loop |
| AIDE, Jiang et al., arXiv 2502.13138 | https://arxiv.org/abs/2502.13138 | Tree search over code solutions with hand-designed draft/debug/improve rules. | L / L / L / L |
| Toledo et al., "AI Research Agents for ML: Search, Exploration, and Generalization in MLE-bench" (AIRA-dojo), arXiv 2507.02554 | https://arxiv.org/abs/2507.02554; NeurIPS 2025 proceedings listing: https://proceedings.neurips.cc/paper_files/paper/2025/hash/328b81881da145412f2bc56c998dfb6a-Abstract-Conference.html | Search policies (Greedy, MCTS, Evolutionary) crossed with operator sets. Not learned. | L–M / L / L / L |
| Foster et al. (… Foerster), "AI Research Preference Models", arXiv 2608.13940 | https://arxiv.org/abs/2608.13940 | Frozen-LM models rank candidates *before execution*, with an inference-only and a pilot-run variant, inside AIRA-dojo. Saves about one-third of the execution budget. | L / **M** (reject-before-run) / L–M / L |
| Yamada et al., "AI Scientist-v2", arXiv 2504.08066 | https://arxiv.org/abs/2504.08066 | Agentic tree search run by an experiment-manager agent. | L / L / L / L |
| ML-Master, arXiv 2506.16499 | Listing only: https://arxiv.org/abs/2506.16499v1 | Exploration combined with reasoning for MLE agents. | L / L / L / L |
| Liang et al., "I-MCTS", arXiv 2502.14693 | https://arxiv.org/abs/2502.14693 | Introspective MCTS with an LLM value model that scores nodes before rollout. | L / L–M / L / L |
| Zhang et al., "Reasoning as Gradient" (Gome), arXiv 2603.01692 | https://arxiv.org/abs/2603.01692 | Whether tree search or directed updates works better depends on model strength. | L / L / L–M / L |
| Liu et al., "ML-Agent", arXiv 2505.23723 (ICML 2026 poster, listing: https://icml.cc/virtual/2026/poster/62020) | https://arxiv.org/abs/2505.23723 | RL-trained 7B MLE agent (the proposer, not a controller). | L / L / L–M / L |
| Zhang et al., "Learning to Ideate for MLE Agents", arXiv 2601.17596 | https://arxiv.org/abs/2601.17596 | RL-trained Qwen3-8B ideator that an implementer can call. | L / L / M / L |
| Yang et al., "Scaling Automatic Research Agents via World Models", arXiv 2608.12564 | https://arxiv.org/abs/2608.12564 | RL post-training of 4B and 9B autoresearch agents, with a world model replacing execution. | L–M / L / L–M / L |
| Jain et al., "AutoResearch-RL", arXiv 2603.07300 | https://arxiv.org/abs/2603.07300 | PPO-updated agent proposes `train.py` edits, with a "termination oracle". Thin evidence; "Claude AI" is listed as an author. | M (RL in autoresearch, over proposals) / L / L / L |
| Qu & Lu, "Bilevel Autoresearch", arXiv 2603.23420 | https://arxiv.org/abs/2603.23420 | An outer LLM loop rewrites the inner loop's search mechanisms at runtime. Parameter-only adjustment gave no reliable gain. | M (meta-control of autoresearch) / L–M / L–M / L |
| Gao, Fang, Zitnik, "AutoScientists", arXiv 2605.28655 | https://arxiv.org/abs/2605.28655 | A decentralised agent team critiques proposals before spending compute. | L / L–M / L / L |
| AlphaEvolve, arXiv 2506.13131 | Listing only: https://arxiv.org/abs/2506.13131.pdf | Evolutionary coding agent. | L / L / L / L |

### 2d. Small learned controllers, routers and orchestrators over LLMs
| Work | Verified | Summary | Overlap |
|---|---|---|---|
| Wen et al., "MetaCtrl", arXiv 2609.37304 | https://arxiv.org/abs/2609.37304 | Lightweight RL-trained controller over a frozen reasoner: continue, simplify, skip or stop. Transfers across backbones. | L / L–M / **M** / L |
| Min et al., "Self-Regulation and Requesting Interventions", arXiv 2502.04576 | https://arxiv.org/abs/2502.04576 | Helper policy decides when to request an intervention under budget C, using offline tabular RL on PRM-labelled transitions. | L–M / L / **M** / L–M |
| Su et al., "ToolOrchestra", arXiv 2511.21689 (ICML 2026 poster, listing: https://icml.cc/virtual/2026/poster/62794) | https://arxiv.org/abs/2511.21689 | RL-trained 8B orchestrator over models and tools, with outcome, efficiency and preference rewards. | L / L / M / L |
| Router-R1, arXiv 2506.09033 (NeurIPS 2025 poster, listing: https://neurips.cc/virtual/2025/poster/119214) | Listing only: https://arxiv.org/abs/2506.09033v3 | RL-trained multi-round routing. | L / L / L–M / L |
| Ghasemabadi et al., "Multi-Head Latent Control", arXiv 2607.14277 | https://arxiv.org/abs/2607.14277 | Heads on frozen hidden states choose defer, clarify, tool or abstain. | L / L–M / M / L |
| Wang et al., "HarnessBridge", arXiv 2606.12882 | https://arxiv.org/abs/2606.12882 | Instruction-tuned plug-in controller that projects observations and accepts or rejects actions. | L–M / L–M / M / L |
| Lin et al., "BAGEN: Are LLM Agents Budget-Aware?", arXiv 2606.00198 | https://arxiv.org/abs/2606.00198 | SFT+RL improves early-stop and alert behaviour. Frontier agents are over-optimistic and keep spending. | L / M (stop) / M / L |
| Yu et al., "Rollback-Induced Reflection" (RIR), arXiv 2609.18304 | https://arxiv.org/abs/2609.18304 | Recovery framed as *when to intervene, where to resume, what knowledge to keep*. Roll the world back and keep a reflection memory. | L / **M** (rollback + memory retention ≈ B's rollback and memory-mode actions) / L / L |
| Fu et al., "CHILL-Harness", arXiv 2607.25825 | https://arxiv.org/abs/2607.25825 | Estimates the advantage of a workflow intervention and applies it only above an advantage margin under a success-preserving constraint. | L–M / M / L–M / M |
| Calibrate-Then-Act, arXiv 2602.16699 | Already in the bib (verified 2026-09-27); listing https://arxiv.org/html/2602.16699v2 | Cost-aware explore/act decisions in LLM agents. | L / L–M / L / L |

### 2e. Branching, replay and counterfactual training data
| Work | Verified | Summary | Overlap on C4 |
|---|---|---|---|
| He et al., "Branching Policy Optimization", arXiv 2607.14171 | https://arxiv.org/abs/2607.14171 | Snapshots the sandbox at high-entropy points and forks siblings; uses sibling-return advantages to train the *agent*. | M (branching is a standard tool) |
| Yu et al. (Manning, Shi), "Shepherd", arXiv 2605.10913 | https://arxiv.org/abs/2605.10913 | Reversible, git-like execution traces. Meta-agents replay from changed points and choose fork points for RL credit. | M (infrastructure prior) |
| Causal Agent Replay 2606.08275; The Replay Gap 2608.08239; Stage-Replay 2607.28495 | See the memo | Branch attribution, replay validity, and KV-cache fidelity. | Stage-Replay and Replay Gap *support* the need for p-aware identification |
| Zhang et al., "RAIL", arXiv 2608.05080 | https://arxiv.org/abs/2608.05080 | Contextual-bandit rollout-intervention allocation in group RL. | L |

### 2f. Noisy keep/discard decisions in iterative experimentation
| Work | Verified | Summary | Relevance |
|---|---|---|---|
| Xu et al., "Phantom Gains: Auditing Self-Improvement Against a Measured Null", arXiv 2608.20290 | https://arxiv.org/abs/2608.20290 | Seven measurement errors that can reverse self-training findings. Needs a measured null per statistic. | Motivation for verify; supports B's noise model |
| Nakajima, "Regimes: held-out-gated improvement loop", arXiv 2606.10241 | https://arxiv.org/abs/2606.10241 | Event-sourced, replayable promote/discard log with held-out gating. One over-promotion is reported. | Close to the *harness* (Paper A / ETAAI) rather than to B's learning |
| Fu et al., "Verify, Don't Trust", arXiv 2609.21257 | https://arxiv.org/abs/2609.21257 | Human-gated verification; replay and mutation tests reject invalid comparisons. | Motivation |
| PACE (§1.4), PrimeScientist max-of-two (§1.3), Centaur seed handling (§1.1) | — | — | The verify arm needs PACE as a baseline |

---

## 3. Overlap verdict per contribution

| Contribution | Verdict | Nearest prior | Reasoning |
|---|---|---|---|
| **C1** loop-level DAC/RL formulation of autoresearch control | **Medium** | Harness-MDP (2607.05458), PrimeScientist (2609.17846), Centaur (2603.24647), ARC (2602.11574), Hyp-RL | I found no paper that casts the *autoresearch keep/discard loop* as DAC with a *trained* intervention policy. But the pieces are all published: "harness as an MDP with a light learned controller", "autoresearch as budgeted sequential decision", and "LLM as online configurator" (AutoEP, LLMZero). C1 is a defensible problem statement, not a headline novelty. |
| **C2** "how to intervene" action space | **Medium** | PACE (verify), Rehearse and AI Research Preference Models (reject before run), RIR (rollback + memory), Hyperband/ASHA/BAGEN (early-stop and stop), PBT and CMA-ES (rollback/step size), Calibration Is Not Control (three-way action) | Every individual action has precedent. Learning *one* typed policy over their union, under one budget, in a noisy training loop, was not found. Novelty is in the composition and the learned trade-off. B must show it through an action ablation. |
| **C3** small configurator vs LLM self-control vs hybrid | **Medium–High risk** | Centaur (0.8B hybrid on autoresearch), COTA (0.5B advisor vs self-reflection), Harness-RL (MLP vs BC / Forced CHECK), MetaCtrl, Self-Regulation, ToolOrchestra | The three-way comparison *in autoresearch* with an explicit LLM-self-control arm was not found. The general claim "a small trained controller complements or beats a big LLM's self-control" is crowded. |
| **C4** counterfactual-branch training/eval with replay-identification guarantees | **High** on branching, **Low** on the guarantee | Calibration Is Not Control, COTA, CIR, BPO, Shepherd | Branch labels for intervention policies are standard by now. I found no prior that carries a quantitative replay-discrepancy allowance (p, 2p, p/(1−p)) into policy learning or evaluation. CIR explicitly states no identification assumptions. CINC discards mismatches. Stage-Replay and Replay Gap show that fidelity cannot be assumed. The guarantee originates in Paper A, so B's novelty is *using* it to train and evaluate a policy. |

---

## 4. Closest 5–8 works and the precise differentiator B must claim

1. **Centaur / Ferreira et al. 2603.24647.** Claim: B *learns* when and how to override, where Centaur's LLM fraction is a fixed r. B's actions act on the accept decision under seed noise (verify, rollback, reject-before-run), which Centaur does not model. Must include Centaur, CMA-ES and TPE on the same nodes and budget.
2. **Harness-MDP / Yi & Song 2607.05458.** Claim: the domain (ML experiment loops with costly, noisy actions and an incumbent), an LLM-self-control arm and a hybrid arm, and paired-branch labels with an identification condition instead of a logged offline buffer. Do *not* claim "learned light harness controller" as new.
3. **PrimeScientist 2609.17846.** Claim: a learned policy instead of a hand-set MCTS exponent, and noise-aware acceptance where PrimeScientist uses max-of-two. Show max-of-two inflating kept gains under the measured seed variance.
4. **PACE 2606.08106.** Claim: verify is one of several actions with a shared budget, and the configurator learns *when* verification is worth its cost. Must include an e-process gate arm.
5. **COTA 2608.21027.** Claim: an explicit replay-discrepancy condition for same-prefix labels where re-execution is stochastic by nature (GPU nondeterminism), a typed multi-action control instead of advice, and the ML-training domain.
6. **CIR 2610.00372 and Calibration Is Not Control 2606.21399.** Claim: p-aware identification (no mismatch discarding, no zero-mismatch assumption), more than binary or three-way actions, and an autoresearch loop.
7. **Rehearse 2607.27687.** Claim: state-dependent learned gating, against an always-on prompted remedy. Use its confidence cliff as motivation for C3 rather than as a B finding.
8. **RIR 2609.18304.** Claim: rollback and memory retention inside a learned multi-action policy over an experiment loop. RIR is a single prompted operator in interactive environments.

---

## 5. The three biggest novelty risks and how to neutralize them

**R1 — "This is HPO/AutoML scheduling with an LLM proposer."**
Every timing action has a classical analog (§2b), and Centaur already runs a classical/LLM hybrid on autoresearch.

Evidence that would neutralize it:
- (a) Same-budget arms for ASHA/successive-halving early-stop, a PACE/racing re-evaluation gate, PBT-style rollback, Centaur and CMA-ES, all on the same nodes.
- (b) An action-ablation table showing that a measurable share of the configurator's gain comes from **content-conditioned** actions with no HPO analog: reject or revise a diff before running, change edit scope, change memory mode.
- (c) Results in the *unconstrained code-edit* regime. Ferreira et al. found that regime is where classical methods cannot represent proposals, though it also narrows LLM-vs-classical gaps.

If the gain comes only from early-stop and verify timing, a reviewer can reasonably call it HPO.

**R2 — "A small trained controller over a frozen LLM is known."**
See Harness-RL, COTA, MetaCtrl, Self-Regulation, ToolOrchestra, ARC and HarnessBridge.

Evidence that would neutralize it:
- Present the controller as the instrument, not the claim.
- Show a specific, preregistered failure of LLM self-control in long campaigns (the Rehearse-style cliff, measured on the harness ledgers).
- Show hybrid > max(LLM-self, configurator) at matched compute.
- Show transfer across nodes and across manager LLMs (DAC instance generalisation on held-out nodes).

**R3 — "Branch-based labels for intervention policies are standard, so C4 is incremental or borrowed from Paper A."**
See CINC, COTA, CIR, BPO and Shepherd.

Evidence that would neutralize it:
- Measure p on the harness itself (re-runs from a restored checkpoint with fixed seeds still diverge on GPU).
- Show at least one decision (a policy ranking or an action's sign) that a naive branch-label learner gets wrong and the p-aware rule fixes.
- Report it in the planted-defect setting the memo already specifies (N1).

Without such a reversal, C4 reads as "we used branching with a caveat". Overlap with Paper A also needs a clean statement to avoid dual-submission concerns.

Secondary risk: autoresearch-control papers are appearing roughly monthly; PrimeScientist (Sept 2026), CIR (Sept 30) and MetaCtrl (Sept 29) are all from the last month. Rerun this sweep before submission.

---

## 6. Most defensible framing

**Recommended: agent-control (oversight/intervention) framing, with the evaluation methodology as its backbone. DAC goes into the related-work vocabulary, not the title.**

- **DAC/AutoML framing (weakest).** It invites R1 directly. AutoML reviewers will expect DACBench-style instance generalisation at a data scale B cannot reach: the B amendment itself counts only about 80 roots and fits ridge heads, not RL. It also makes Hyperband, ASHA, PBT and Centaur the natural baselines. DAC buys vocabulary but no theorem, as the 2026-10-04 amendment §1 already concedes.
- **Agent-control framing (best fit).** The nearest learned-controller priors (Harness-RL, COTA, CIR, CINC, MetaCtrl) all run on agent benchmarks with near-deterministic replay and cheap actions. B's distinctive setting is the *autoresearch loop*: noisy keep/discard on an incumbent, expensive runs, intervention types that include verify-by-reseed and rollback, and an LLM proposer whose self-control is documented to degrade (Rehearse). In this setting, C2 and C3 have a clear, testable story, and classical HPO controllers become *baselines* rather than the frame.
- **Evaluation-methodology framing.** This is the most novel piece in isolation, because the p-aware identification was not found elsewhere. But it belongs to Paper A. Putting it in the headline of B risks overlap with A. Use it as B's measurement section ("how we can trust the learned policy's estimated gains"), and cite A.

A plausible one-line framing: *"Learning when and how to intervene in noisy autoresearch loops: a configurator for keep/verify/rollback/stop, evaluated by p-aware paired branches."*

---

## 7. Venue check (as of 2026-10-09)

| Venue | Status | Key dates | Source | Fit for this paper |
|---|---|---|---|---|
| **ICML 2027** | **CFP not published** | Official: location "South America", no city or dates (FutureMeetings). Typical window from ICML 2026: abstract 23 Jan, full paper 28 Jan, notification 30 Apr, conference 7–11 Jul 2026. Unofficial estimate: abstract 16 Jan, full paper 22 Jan 2027 (OpenCurious, marked "Not yet official"). | https://icml.cc/Conferences/FutureMeetings ; https://icml.cc/Conferences/2026/Dates ; https://www.opencurious.com/ai-conference-deadlines/icml-2027 | Good fit for the agent-control/RL framing. Expect reviewers to demand the HPO and agent-controller baselines (R1, R2). |
| **NeurIPS 2027** | **Not announced** | Official: "Europe", no city or dates. Typical window from NeurIPS 2026: abstract 4 May, full paper 6 May, notification 24 Sep, conference 6–13 Dec 2026. Unofficial estimate: 14/21 May 2027 (OpenCurious, "Not yet official"). | https://neurips.cc/Conferences/FutureMeetings ; https://nips.cc/Conferences/2026/Dates ; https://www.opencurious.com/ai-conference-deadlines/neurips-2027 | Good fit, and it gives about 4 more months to collect counterfactual-branch data. |
| **ICLR 2027** | **Main deadline passed** | Abstract 18 Sep 2026; paper 25 Sep 2026; reviews 5 Nov; final decisions 16 Dec 2026; conference 26–30 Apr 2027, California (venue TBC). Workshop track: proposals due 9 Oct 2026, acceptance 29 Nov 2026, suggested workshop-paper deadline 1 Feb 2027. | https://www.iclr.cc/Conferences/2027/CallForPapers ; https://iclr.cc/Conferences/2027/index.html ; https://iclr.cc/Conferences/2027/CallForWorkshops | Main track is closed. An ICLR 2027 workshop (agents, AI-for-science, or AutoML themed, if accepted) is a realistic early outlet around Feb 2027. Workshop list due by 29 Nov 2026. |
| **AAAI-27** | **Main deadline passed** | Abstract 21 Jul; full paper 28 Jul 2026; Phase-1 notification 24 Sep; author feedback 19–25 Oct; final notification 30 Nov 2026; conference 16–23 Feb 2027, Montréal. Workshops: accepted list due 16 Oct 2026; workshop submissions due 20 Nov 2026 (organisers may set their own deadlines); notifications 2 Dec; workshops 22–23 Feb 2027. | https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/ ; https://aaai.org/conference/aaai/aaai-27/workshops-call/ | Main track is closed. AAAI-27 workshops (list posts 16 Oct) are an option on a 20 Nov 2026 timescale if a relevant workshop is accepted. |
| **AutoML Conf 2027** | **Not announced** (2027.automl.cc not fetchable; no 2027 CFP found) | Typical window from AutoML 2026: submission 14 May 2026 (CFP first said 30 Apr; extended), notification 26 Jun, camera-ready 30 Jul, conference 28 Sep–1 Oct 2026, Ljubljana. | https://2026.automl.cc/dates/ ; https://groups.google.com/g/coseal/c/P4epSYWznq0 ; https://eurai.org/sponsored-conference/automl | Fits **only** under the DAC/AutoML framing (Methods track). Its reviewers are best placed to press R1. |
| **TMLR** | Rolling | Rolling submissions on OpenReview; paused over holidays; "technical correctness over subjective significance". | https://jmlr.org/tmlr/ | Safe route if the empirical scale stays modest. Paper A is already going there, so check scope overlap. |
| **JMLR** | Rolling | Own submission system; no deadlines; no simultaneous submission; papers over 35 pages take longer and over 50 pages need a justification. | https://www.jmlr.org/author-info.html | Poor fit unless the theory (Q^ρ vs Q*, observed vs full state, identification) becomes the main contribution. |
| 2027 workshops | Mostly **not yet announced** | ICLR 2027 workshop list due 29 Nov 2026; AAAI-27 list due 16 Oct 2026. ICML 2027 and NeurIPS 2027 workshops are unannounced. | Same as above | Check again after 16 Oct and 29 Nov 2026. |

All dates are AoE where the source says so. Nothing in the "not announced" rows is a guess; typical windows are labelled as prior-year reference values.
