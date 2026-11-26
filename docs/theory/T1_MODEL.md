# T1 — The governed loop as noisy sequential selection with an incumbent

> **Historical protocol context.** The 12 Oct fixed-split and frozen-response descriptions below are historical. PLAN §10 later adopts `vary` and the D4 amendment. A ledger-dependent proposer can create feedback; whether decision independence holds is a condition to examine, not an automatic empirical finding. The theory remains unchecked by the author.

*Theory track T1 (RUNBOOK §3, added 12 Oct 2026). Drafted 12 Oct 2026 by an AI agent (Claude) at the author's request; AI-assisted, not reviewed by a human. Nothing here is evidence. Citations marked [v] were checked against a publisher, proceedings or arXiv page on 12 Oct 2026; the others are standard references that still need a check before they enter a manuscript.*

## 1. The loop as the harness implements it

Facts established in the harness code (branch `r1`, `src/autoresearch/control_plane/`):

1. A campaign is a sequence of trials. In each trial the manager proposes one bounded edit of the editable files; the worker applies it and runs the node; the control plane parses one metric.
2. **Keep rule ρ** (`decision.py`): keep iff the parsed metric strictly beats `current_best`. On a non-keep the editable files are restored, so the workspace always holds the best *observed* configuration.
3. **`current_best` is a stale, selected draw.** It is the metric recorded when the incumbent was kept, never re-measured.
4. **Seeds are fixed for the whole campaign.** Training seed and split seed default to constants (now injectable as `AR_TRAIN_SEED` / `AR_SPLIT_SEED`). On CPU nodes a re-run at the same seeds reproduces the metric bit-for-bit (STATUS, L7/L8).
5. **Verify** (`_run_verify`) re-runs candidate and incumbent at r paired fresh training seeds. Under the default `"fixed"` split policy the split seed is *not* resampled. The frozen response keeps iff the mean paired difference is positive.

## 2. Model

**Configurations and value.** Let 𝒞 be the bounded configuration space. Each run evaluates configuration c under randomness ω = (ω_train, ω_split, ω_hw):

  m(c, ω) = J(c) + η(c, ω),  J(c) = E_ω[m(c, ω)].

J is the quality the campaign should improve. η has variance σ²(c) and, for two configurations evaluated at the same ω, correlation ϱ(c, c′).

**Two observation regimes.**
- **Common-random-numbers (CRN) regime** — CPU nodes as the harness runs them. Every run in a campaign uses the same ω₀, so the campaign sees the deterministic surrogate J̃(c) = m(c, ω₀). The error J̃ − J is fixed per configuration, not resampled. Re-running at ω₀ removes nothing.
- **Fresh-draw regime** — GPU nodes and timing-based metrics (autoresearch, `mlagentbench_vectorization`). Each run draws a fresh ω_t.

**Proposal law.** c_t ∼ P(· | H_{t−1}), where H is the ledger prefix. In practice c_t = c_inc ⊕ e_t is a local edit of the incumbent, and P depends on H through the memory context. This feedback is what separates the loop from every classical selection model (§4).

**Increment and its estimate.** True increment Δ_t = J(c_t) − J(c_inc). Observed increment Δ̂_t = m(c_t, ω_t) − B_t, where B_t = `current_best`.
- In the CRN regime, Δ̂_t − Δ_t = η(c_t, ω₀) − η(c_inc, ω₀), with variance σ_Δ² = 2σ²(1 − ϱ) when the two variances are equal.
- In the fresh-draw regime, B_t is the maximum of the noisy draws that were kept, so E[B_t] > J(c_inc) (winner's curse; §3 F2).

**Actions** (PLAN §4, D3). At E1: continue, skip, revise. At E2: continue (apply ρ), verify(r) (r paired fresh-seed differences D_i = m(c_t, ω_i) − m(c_inc, ω_i), keep iff D̄ > 0), and the threshold rule ρ_z (keep iff Δ̂_t > z·σ̂_Δ; a policy, not a harness action). At E0: stop, demote.

**Budget and objective.** The budget C counts worker runs (verify(r) costs 2r runs) plus an LLM-call cap. The objective is the audited improvement Y = J(c_inc,T) − J(c₀), normalised per node. This is a *simple-regret* objective: only the final incumbent counts.

## 3. Structural facts the theory must respect

- **F1 — CRN turns noise into bias.** With ω₀ fixed, the loop is a deterministic hill-climb on J̃. A false keep is overfitting of ω₀; it never shows up as non-reproducibility. This is adaptive overfitting of a reused validation split (Cawley & Talbot 2010 [v]; Dwork et al. 2015; Blum & Hardt 2015 [v]). Only fresh ω can detect it. A verify that resamples only ω_train leaves the ω_split part of the error untouched. Whether that matters is a per-node number (E1).
- **F2 — the incumbent is a selected maximum.** In the fresh-draw regime B_t is biased upward. Consequences: more later true improvements are rejected (stagnation), and the reported in-run gain overstates Y. This is the optimizer's curse (Smith & Winkler 2006 [v]).
- **F3 — counter-evidence on re-evaluation.** For evolutionary algorithms, not re-evaluating the parent can be *more* robust: on LeadingOnes the (1+1) EA without re-evaluations tolerates constant noise rates, against O(n⁻² log n) with them (Antipov & Doerr 2024, arXiv 2409.00306 [v]). Qian, Yu & Zhou (arXiv 1311.4987 [v]) show re-evaluation and threshold selection can both be ineffective, and that a modified threshold rule can help. So "verify more" is not automatically good. T2 must say *when* it helps, and E1b must allow it to lose.
- **F4 — arms arrive online and depend on the past.** There is no fixed arm set. The proposer is a reservoir conditioned on H, so a decision changes the future arm distribution.

## 4. Literature map: what each line assumes and where the loop departs

| Line | Core object and result | Assumes | Where the loop departs | Use in R1 |
|---|---|---|---|---|
| **Ranking & selection** (indifference zone: Bechhofer 1954; fully sequential: Kim & Nelson 2001; OCBA: Chen et al. 2000 [v]) | Allocate samples among k fixed systems to select the best with guaranteed probability of correct selection | Fixed finite set; independent or CRN samples; selection at the end | Systems arrive one at a time as local edits; incumbent-vs-challenger only; budget shared with exploration | Pairwise IZ logic gives the verify sample size r for a target error at margin δ |
| **Knowledge gradient** (Frazier, Powell & Dayanik 2008 [v], SIAM J. Control Optim.; correlated beliefs, INFORMS J. Comput. 2009 [v]) | One-step look-ahead value of a measurement under Gaussian beliefs | Finite alternatives; known noise variance; Bayesian prior | Alternatives generated online; value accrues only through the final incumbent | **KG-style index** for verify: expected gain in E[J(c_inc,final)] from r paired runs, compared with its run cost (T2) |
| **Racing** (Hoeffding races: Maron & Moore 1994/1997; F-Race: Birattari et al. 2002 [v]; irace: López-Ibáñez et al. 2016 [v]) | Evaluate candidates on a growing instance set; drop those that are statistically worse | Candidate pool fixed per race; instances are the noise source | Pool of two (incumbent, challenger) at each step; races must end inside one trial | **Racing-style baseline:** keep sampling paired seeds until a sequential test separates the pair or a cap is hit |
| **Best-arm identification** (Even-Dar, Mannor & Mansour 2006; Audibert, Bubeck & Munos 2010; Kaufmann, Cappé & Garivier 2016; infinitely many arms, simple regret: Carpentier & Valko 2015 [v]) | Sample complexity of finding the best arm (fixed confidence or fixed budget) | Stationary arms; for infinitely many arms, i.i.d. arm draws from a reservoir | The reservoir is the proposer and changes with H; arms cost one run to draw *and* to sample | Carpentier & Valko is the nearest formal analogue: draw new arms vs re-sample known ones, under simple regret |
| **Anytime-valid testing** (Ramdas et al. 2023, Statistical Science; PACE, arXiv 2606.08106 [v]) | e-process commit gate: bounds false-commit probability under optional stopping | Paired evaluations on identical instances | Per-candidate guarantee, not a campaign-level value | **PACE-style baseline** and one D23 candidate |
| **Adaptive overfitting of a holdout** (Dwork et al. 2015, Science; the Ladder: Blum & Hardt 2015 [v]) | Re-using a holdout adaptively overfits it; the Ladder updates the leaderboard only when the gain exceeds a threshold | Fixed holdout, many adaptive submissions | Same structure as the CRN regime (F1) | **Ladder-style threshold** is the theory-backed form of the noise-aware threshold baseline |
| **Optimizer's curse** (Smith & Winkler 2006 [v]) | The selected maximum of noisy estimates is biased upward; shrinkage corrects it | Estimates of several alternatives, choose the maximum | Sequential version: the bias compounds through B_t | Bias of `current_best` and its effect on later acceptance (T2-ii) |
| **Noisy evolutionary optimisation** (Qian, Yu & Zhou, arXiv 1311.4987 [v]; Antipov & Doerr, arXiv 2409.00306 [v]) | Runtime of the (1+1) EA under noise, with and without re-evaluation | Pseudo-Boolean benchmarks, bit-flip mutation | Continuous metrics, LLM proposer, budget in runs | Closest analogue of an incumbent loop; supplies the counter-hypothesis F3 |
| **Noisy Bayesian optimisation** (noisy EI: Letham et al. 2019, Bayesian Analysis [v]) | Integrates over the noisy incumbent value instead of trusting the observed best | GP surrogate | No surrogate over the edit space in the harness | Motivates a posterior-mean incumbent B̃ instead of the raw maximum |

**What R1 adds.** No line above covers all four features together: incumbent-vs-challenger with restore, arms generated by a feedback proposer, CRN-fixed seeds that turn noise into bias, and a single campaign budget shared between drawing new arms and re-sampling old ones. The cleanest formal home is a sequential, budgeted version of the Carpentier–Valko reservoir problem with a two-arm racing step inside each trial. T2 starts from the one-trial version, which is analytically tractable.

## 5. Hypotheses for T2 and the pilots

- **H1 (error rate).** In the CRN regime with Gaussian η, the default rule errs on an edit of true size Δ with probability Φ(−|Δ|/σ_Δ). E1 measures σ_Δ and |Δ| per node.
- **H2 (verify can only fix what it resamples).** With the `"fixed"` split policy, verify reduces the error only through the ω_train component. If σ_Δ,train ≪ σ_Δ,split on a node, verify(fixed) is nearly worthless there and `"vary"` is required (D21).
- **H3 (stagnation).** In the fresh-draw regime, the acceptance rate of true improvements of size δ falls as the campaign proceeds, because B_t − J(c_inc) grows with the number of keeps. A posterior-mean or re-measured incumbent removes the trend.
- **H4 (no free verification).** Under a fixed run budget, the value of verify(r) is positive only when |Δ̂|/σ_Δ is near zero and the remaining budget is small enough that a false keep cannot be undone later. Far from the boundary, a fresh proposal is worth more than a re-sample (the F3 regime).

## References

- Antipov, D. & Doerr, B. (2024). Evolutionary algorithms are significantly more robust to noise when they ignore it. arXiv:2409.00306. [v]
- Audibert, J.-Y., Bubeck, S. & Munos, R. (2010). Best arm identification in multi-armed bandits. COLT.
- Bechhofer, R. E. (1954). A single-sample multiple decision procedure for ranking means of normal populations with known variances. Ann. Math. Statist. 25(1).
- Birattari, M., Stützle, T., Paquete, L. & Varrentrapp, K. (2002). A racing algorithm for configuring metaheuristics. GECCO. [v]
- Blum, A. & Hardt, M. (2015). The Ladder: a reliable leaderboard for machine learning competitions. ICML, PMLR 37. arXiv:1502.04585. [v]
- Carpentier, A. & Valko, M. (2015). Simple regret for infinitely many armed bandits. ICML, PMLR 37. arXiv:1505.04627. [v]
- Cawley, G. C. & Talbot, N. L. C. (2010). On over-fitting in model selection and subsequent selection bias in performance evaluation. JMLR 11. [v]
- Chen, C.-H., Lin, J., Yücesan, E. & Chick, S. E. (2000). Simulation budget allocation for further enhancing the efficiency of ordinal optimization. Discrete Event Dyn. Syst. 10. doi:10.1023/A:1008349927281. [v]
- Dwork, C., Feldman, V., Hardt, M., Pitassi, T., Reingold, O. & Roth, A. (2015). The reusable holdout: preserving validity in adaptive data analysis. Science 349.
- Even-Dar, E., Mannor, S. & Mansour, Y. (2006). Action elimination and stopping conditions for the multi-armed bandit and reinforcement learning problems. JMLR 7.
- Frazier, P. I., Powell, W. B. & Dayanik, S. (2008). A knowledge-gradient policy for sequential information collection. SIAM J. Control Optim. 47(5). [v]
- Frazier, P. I., Powell, W. B. & Dayanik, S. (2009). The knowledge-gradient policy for correlated normal beliefs. INFORMS J. Comput. 21(4). [v]
- Kaufmann, E., Cappé, O. & Garivier, A. (2016). On the complexity of best-arm identification in multi-armed bandit models. JMLR 17.
- Kim, S.-H. & Nelson, B. L. (2001). A fully sequential procedure for indifference-zone selection in simulation. ACM TOMACS 11(3).
- Letham, B., Karrer, B., Ottoni, G. & Bakshy, E. (2019). Constrained Bayesian optimization with noisy experiments. Bayesian Analysis 14(2). arXiv:1706.07094. [v]
- López-Ibáñez, M., Dubois-Lacoste, J., Pérez Cáceres, L., Birattari, M. & Stützle, T. (2016). The irace package: iterated racing for automatic algorithm configuration. Oper. Res. Perspect. 3. [v]
- Maron, O. & Moore, A. W. (1997). The racing algorithm: model selection for lazy learners. Artif. Intell. Rev. 11.
- Qian, C., Yu, Y. & Zhou, Z.-H. Analyzing evolutionary optimization in noisy environments. arXiv:1311.4987. [v]
- Ramdas, A., Grünwald, P., Vovk, V. & Shafer, G. (2023). Game-theoretic statistics and safe anytime-valid inference. Statistical Science 38(4).
- Shawn, Z. (2026). PACE: anytime-valid acceptance tests for self-evolving agents. arXiv:2606.08106. [v]
- Smith, J. E. & Winkler, R. L. (2006). The optimizer's curse: skepticism and postdecision surprise in decision analysis. Management Science 52(3). [v]
