# Problem specification (draft): learned control of governed autoresearch loops

*Design memo for the Paper B pivot. Draft of 9 Oct 2026. Not a paper section; nothing here is evidence. Nothing in it is adopted until the author decides §9.*

**Tags.** **[E file:line]** means established in a source file. **[P]** means my proposal. **[NEW]** means the harness needs code it does not have. Harness paths are relative to `autoresearch_harness/`. `A/…` means `agent_sys_paper/papers/paper_a/`. `MDP` means `agent_sys_paper/notes/mdp_framing/MDP_FRAMING.md`. `B/…` means `agent_paper_B/`.

---

## 0. One-paragraph statement

A governed campaign is a sequence of trials. In each trial a manager LLM proposes one bounded edit, a worker applies it and trains, and the control plane keeps the edit only if the parsed metric strictly beats the incumbent **[E `src/autoresearch/control_plane/campaign.py:502-720`, `decision.py:54-66`]**. **[P]** We add a *configurator*: a policy that, at fixed points inside each trial, picks one control action from a masked set: execute, skip, revise, verify, and later stop or change scope. It is trained to maximise the true quality of the final incumbent under a compute budget. The configurator is compared with the LLM making the same control decisions itself, and with hybrids, at matched budgets. Paper A supplies the theory for training on branched (restored) states. Deployment comparisons need no restoration, so Paper A's allowance $p$ qualifies *training labels and diagnostics*, not the primary contrasts. This fixes Paper B's main weakness, where the N1 tax $12p$ swamped every effect **[E B/docs/paper_split/RUNBOOK.md:790-796]**.

---

## 1. Setting

### 1.1 Instance, episode, budget

- **Instance** $\iota=(n,\sigma,\mu,C,c_0)$ **[P]**:
  - node $n$, whose YAML is in `configs/nodes/`;
  - instance seed $\sigma$;
  - manager $\mu$ (model, backend, temperature, memory mode);
  - compute budget $C$;
  - starting configuration $c_0$, the node baseline restored by `scripts/reset_node_state.py`.
- **Seed policy today [E].**
  - The training seed is a constant inside node code: `SEED = 123` in `nodes/ResNet_trigger/train.py:54`, `SEED = 42` in `nodes/openml_*/benchmark.py:23` (a frozen file), and `torch.manual_seed(42)` in autoresearch `train.py:510`.
  - Replicate campaigns so far differ only by LLM sampling: "fixed training seed per campaign (123), LLM stochasticity provides seed variation" **[E plan/archive/paper_edit_checklist.md:93]**.
  - So $\sigma$ needs a seed-injection path **[NEW]**.
  - On ResNet the seed also fixes the train/val/test split **[E nodes/ResNet_trigger/prepare.py:165-180]**.
- **Episode.** One campaign of trials $t=1,\dots,T$.
  - Today $T$ is a trial count: `BudgetState` counts trials, and every trial, including failed ones, consumes one **[E control_plane/budget.py:77-101; campaign.py:720]**.
  - **[P]** Make the binding budget compute (worker runs or worker-seconds) plus a cap on LLM calls. Then $T$ is random. This is needed because "skip" and "verify" make sense only if they change spend (§2).
- **Default control $\rho$.** The current rule:
  - execute every proposal that passes the precondition check;
  - keep iff $\Delta>0$ on the single parsed metric;
  - restore editable files on non-keep;
  - no re-evaluation.
  
  **[E campaign.py:585-590, 715-719; decision.py:54-66]**. As in Paper A, $\rho$ and the manager $\mu$ are part of the environment, not of the controller **[E MDP:19]**.

### 1.2 Decision epochs inside one trial

| Epoch | Location in `run_real_campaign` (`campaign.py`) | Exists? | Information available |
|---|---|---|---|
| $E_0$ pre-proposal | before `build_memory_context`, :513 | loop point exists; no hook **[NEW]** | ledger prefix, workspace constants, budget |
| $E_1$ post-proposal, pre-execution | after `_precondition_failure_result` returns `None` (:585-588), before `worker.run_trial` (:590). The guard (:562) and snapshot (:584) are already taken. | no hook **[NEW]** | + `ManagerProposal`: summary, rationale, objective, `extra.structured_edit` {symbol, old, new, effective_key} |
| $E_2$ post-metric, pre-commit | `decide_trial` runs *inside* `_record_from_worker_result` (:1014-1020). The record is appended at :698 and restore/incumbent update happen at :715-719. | no hook. **[NEW]** Split "evaluate" from "commit" so an action can precede the immutable append. | + `WorkerResult`: metric, validity, failure category, $\Delta$ vs best, logs, wall-clock |
| $E_{1.5}$ mid-run | inside the worker subprocess (`local_worker.py:263-270`, `claw_worker.py:463`) | **absent**. Runs are blocking `subprocess.run` with a timeout. | would need a streaming metric |

**[P]** The decision process indexes epochs $k=(t,e)$ with $e\in\{0,1,2\}$. $E_{1.5}$ is an extension only.

---

## 2. Action space: how to intervene

### 2.1 Candidate actions

Costs are in units of one worker run $w_n$ and one manager call $\ell$. Runtime per worker run **[E `expected_runtime` in configs/nodes/*.yaml]**:

- lr_synthetic: seconds;
- OpenML: 2-15 s;
- MLAgentBench: 0.1-3 s;
- ResNet fast mode: minutes on CPU;
- autoresearch: about 5 min (`TIME_BUDGET = 300` s, `prepare.py:43`).

LLM call latency and cost are not recorded in the staged files and must be measured. On CPU nodes $\ell$ can dominate $w_n$.

| # | Action (epoch) | What it changes | Hook / new code | Cost | Mask: feasible iff | Branch-identifiable? |
|---|---|---|---|---|---|---|
| a0 | **continue** (all) | nothing; $\rho$ | none | 0 | always (Paper A's baseline availability, **[E A/sections/06a_theory.tex:22-28]**) | reference arm |
| a1 | **skip** ($E_1$) | proposal is logged and not executed; workspace unchanged | **[NEW]** new terminal `skipped` state. The state machine has only kept/discarded/failed_invalid **[E state_machine.py:9-19]**. Skips must still be ledgered (governance invariant). | saves $w_n$; $\ell$ already spent | proposal passed precondition; budget unit is compute | yes, one-step from the $E_1$ state |
| a2 | **revise** ($E_1$) | re-calls the manager once with structured feedback (e.g. "repeated direction", "too large a step") | **[NEW]** feedback field in `_prepare_context` (`langgraph_manager.py:42-109` has none). The baseline/prompt managers are deterministic and cannot revise. | $+\ell$ | revisions for this trial $<1$; LLM-call cap left; LLM manager | yes; revision sampling is part of the kernel |
| a3 | **verify** ($E_2$) | re-runs candidate (and, paired, incumbent) at $r$ fresh seeds. A **frozen response rule** keeps iff mean paired $\Delta>0$. It can therefore *veto* a keep or *rescue* a discard. | **[NEW]** seed injection per node plus re-run of the incumbent from the stored patch. `scripts/reexecute_kept_trials.py` does an offline version for LocalWorker. | $r$ or $2r$ runs | trial valid; seed injection supported; compute left $\ge$ cost | yes, from the $E_2$ state |
| a4 | **demote** ($E_0$) | reverts the last *unverified* keep to the previous incumbent | **[NEW]** incumbent stack. Today only a per-trial snapshot of editable files exists (`campaign.py:204-225`). Patches are stored per trial, so replay from `.autoresearch_baseline` is possible. | 0-1 runs | a previous incumbent exists | yes |
| a5 | **stop** ($E_0$) | ends the campaign; unspent compute is returned | small **[NEW]** | $-$remaining | $t\ge t_{\min}$ | value of stopping needs no branch; the contrast needs continuations |
| a6 | **scope / step size** ($E_0$) | constrains the next proposal's symbol subset or step magnitude | **[NEW]** prompt and selector constraints | 0 | LLM manager | only as a persistent regime (option) |
| a7 | **memory-mode switch** ($E_0$) | changes the `MemoryMode` passed to `build_memory_context` | small **[NEW]**. Mode is a per-campaign argument today, but the builder takes it per call (`campaign.py:513-516`). | 0 | always | only as a persistent regime |
| a8 | **low fidelity / early stop** ($E_1$/$E_{1.5}$) | screens at reduced fidelity, then promotes | ResNet has fidelity env vars (`RESNET_TRIGGER_FAST_*`, `train.py:82-89`). True early stopping needs a streaming worker **[NEW]**. | fraction of $w_n$ | node exposes fidelity | **no** for mid-run states. Model/optimiser state is not restorable in the harness; evaluate with common random numbers instead. |
| a9 | **accept-worse** ($E_2$) | keeps a non-improving candidate (exploration) | changes `decide_trial`'s invariant | 0 | — | yes |

Note a fact that shapes the set. Because keep requires strict improvement and non-keeps are restored, the workspace always holds the best *observed* config. **"Rollback to best" is therefore a no-op under $\rho$.** It becomes meaningful only after verification exposes a noise keep (a4), or if a9 is allowed.

### 2.2 What must be restored to branch (Paper A's state layers)

Paper A's state boundary lists workspace, environment, session history, budget and external tools, and says inference caches and sampling randomness need explicit treatment **[E A/submission_sections/03_instrument.tex:113-119]**. Mapped to the harness:

| Layer | In harness | Audited today? | Restore path |
|---|---|---|---|
| Editable files | `editable_paths` | yes. `node_state_hash` (SHA-256 of editable files) is recorded per trial **[E schemas.py:296-303; claw_worker.py:155]**. | snapshot, or replay kept patches from baseline |
| Non-editable node state | `artifacts/`, `results.tsv`, `experiment_memory.jsonl`, `.autoresearch_artifacts/`, `run.log`, OpenML cache | **no** | `reset_node_state.py` (for baseline only) |
| git / worktree | the claw worker diffs against the working tree (`claw_worker.py:154`) | partly (`git_commit_before/after`) | `scripts/create_trial_worktree.py` gives isolation |
| Ledger / memory | prefix of the JSONL ledger; drives memory context, `current_best` and budget | yes (append-only, provenance) | copy the prefix to a branch campaign id. **Caveat:** `_current_best` recomputes from *all* records with a metric, including `failed_invalid` ones (metrics are stored even when invalid, :1043), and uses `max` regardless of `metric_direction` (:1136-1138). On minimise nodes, or with an invalid trial that carries a high metric, the resumed `current_best` differs from the in-run value. This is a concrete outcome-relevant discrepancy. **[NEW]** Restore `current_best` explicitly. |
| RNG | training seed in a node file; per-run RNG re-seeded inside training | via files | files; GPU nondeterminism cannot be restored (kernel noise, §4.4) |
| LLM backend | Ollama local model or DeepSeek API; temperature 0.2 (`langgraph_manager.py:257`) | model id only | pin a local model digest. An API model can drift between the original run and a branch, which is a discrepancy $D$, not noise. |

There is a precedent from the harness's own history. A reset defect contaminated ResNet seeds s4/s5 and was caught by per-trial hashes **[E plan/revision_6.md:46-49; priority0_report.md:33]**. In Paper A's terms, that was a discrepancy on an audited layer. Non-editable state is the unaudited layer $\mathcal L_Y\setminus\mathcal L_A$.

### 2.3 Recommended core set [P]

Core set: **{continue, skip, revise, verify (with demote as part of its frozen response rule)}**. Add **stop** only if the budget unit is compute (§9, D1).

Reasons:

1. All four are one-step deviations at $E_1$/$E_2$, so Paper A's branch identification applies directly.
2. Each targets a mechanism that the default rule already produces and that is **not planted**. This answers B's critique M-1 **[E B/RUNBOOK.md:811-833]**.
   - **Invalid or wasted runs.** On autoresearch summary-arm seeds, the invalid rate (IR) was 0.10-0.30 on healthy seeds and 1.00 on one seed **[E plan/archive/autoresearch_analysis.md:25-37]**. This is what skip and revise address.
   - **Winner's-curse keeps under seed noise.** This is what verify and demote address (§4.4).
3. They separate "when" from "how". Verify is B's timing question moved into a natural setting: verify at keep time, or reserve the budget for later.

Extensions, in priority order:

- **a6 scope** — the purest "how", but it is a persistent regime, its effect runs through the LLM, and it is identifiable only as an option;
- **a8 fidelity/early stop** — the classical HPO baselines live here;
- **a7 memory switch**;
- **a9 accept-worse**.

---

## 3. State and information

- **Full state $X_k$:**
  - all layers in §2.2;
  - the current proposal or worker result;
  - remaining budget;
  - LLM backend state;
  - the instance's latent response surface $J(\cdot)$ (true generalisation of every config). This is constant within an episode, like Paper A's stratum $J$.
- **Recorded history $H_k$:**
  - the ledger prefix;
  - the current proposal (at $E_1$) or `WorkerResult` (at $E_2$);
  - the event stream (`events.py`);
  - budget counters.
- **Fact established by construction [E campaign.py:513-541; langgraph_manager.py:278-295].** The LangGraph manager keeps no state across calls. Its input is a deterministic function of the ledger prefix, the memory mode, the editable constants and the node spec. Given $H_k$, the manager's next proposal is therefore fixed up to LLM sampling and backend state. This is the closest the system comes to a Markov property. **[P]** Do not claim a Markov property for any compressed $Z$, following the standing stance **[E B/docs/paper_split/RUNBOOK.md:627-631; B/papers/paper_b/sections/02_problem.tex:28-35]**.
- **$Z_k=f(H_k)$, the configurator view [P].**
  - Structured ledger features: index $t$, remaining compute and LLM calls, `current_best`, the history of $\Delta$ and decisions, failure-category counts, `repeated_bad_count`, wall-clock, verify outcomes so far.
  - The proposal's structured edit (symbol, direction, log step size, effective-config change).
  - At $E_2$: metric, $\Delta$, validity.
  - Optionally the same text the manager saw: memory context, summary and rationale.
- **Mask $M_k$** as in §2.1. Recorded before the action, as in Paper A's availability rule **[E A/submission_sections/02_decision_estimands.tex:13-23]**.
- **What the manager LLM sees [E langgraph_manager.py:47-107].**
  - Node, metric and direction, editable files and constants, trial index, current best, memory text.
  - **Not** the total budget, and no control-action menu.
- **What the configurator must not see:**
  - audit or test metrics;
  - outcomes of sibling branches;
  - future ledger entries;
  - other arms' runs.
- **Elapsed step [P, needs confirmation].** The standing decision refuses elapsed step in Paper A's *registered cell* $Z$. The reasons were cell-count blow-up and re-registering `thm:refinement` **[E MDP:161]**. The configurator's $Z$ is a different object, a function approximator rather than a gate partition. Budget-coupled timing depends on remaining budget, and B's controllers already saw "remaining budget and progress" **[E B/docs/paper_split/B_CONTROLLER_DESIGN_20260927.md:§4]**. I propose including remaining budget in the configurator's $Z$. This does not reopen A's decision (§9, D9).

---

## 4. Reward, cost, harm, noise

### 4.1 Objective

- **Target.** Let $J(c)=\mathbb E_\omega[m(c,\omega)]$, with the sign set so that larger is better. Here $\omega$ is the seed or split together with hardware nondeterminism. Where a held-out test split exists, use its expectation instead. ResNet and OpenML both have test splits **[E configs/nodes/openml_*.yaml `split`]**, although ResNet's fast mode skips test (`RESNET_TRIGGER_FAST_SKIP_TEST=1`, README:283).
- **[P] Terminal outcome.** $Y=\big(\widehat J_{\text{audit}}(c^{\text{inc}}_T)-\widehat J_{\text{audit}}(c_0)\big)/(U_n-L_n)$, clipped to $[-1,1]$.
  - $\widehat J_{\text{audit}}$ re-evaluates the incumbent at $K$ fresh seeds, with the same seeds for every arm (common random numbers), outside the campaign budget.
  - $[L_n,U_n]$ is a declared per-node range, needed for Paper A's range normalisation **[E A/submission_sections/03b_measurements.tex:117-127]**.
  - The in-campaign `current_best` is **not** the outcome, because selection biases it upward.
- **Secondary binary outcome.** $S=\mathbf 1\{Y>\delta_n\}$, for Paper A's sharp $R=1$ binary result.

### 4.2 Cost and constraint

Per-trial cost vector:

$$c_t=(\text{worker-s},\ \#\text{runs},\ \text{manager tokens/calls},\ \text{control tokens (side queries)},\ \text{configurator inference})$$

- **[P] Primary constraint:** a hard per-campaign compute budget $C$ (worker runs, or seconds on mixed-speed nodes) and a cap on LLM calls.
- Optional intervention cap $B_{\text{int}}=\lfloor qT_0\rfloor$ on verify runs, kept for comparability with B.
- Report net gain per compute as a secondary.

### 4.3 Harm events

Harm is defined relative to $J$, not the in-run metric:

- **false keep:** kept but $J(c_t)\le J(c^{\text{inc}})$;
- **false discard:** discarded or skipped but $J(c_t)>J(c^{\text{inc}})$;
- **wasted run:** executed, then `failed_invalid`;
- **mean harm:** $\mathbb E[Y^\pi-Y^\rho]<0$ on any node.

All are measurable offline by auditing the ledgered candidates at fresh seeds.

### 4.4 How seed noise enters keep/discard

Write $m(c,\omega)=J(c)+\eta(c,\omega)$ with $\operatorname{Var}\eta=\sigma_n^2$. The harness compares $\hat\Delta=m(c_t,\omega_t)-\texttt{current\_best}$.

- **Deterministic CPU nodes with a fixed seed.** Here $\omega_t=\omega_0$, so the comparison uses common random numbers and re-running gives the identical number. The error is *selection on one realisation*. Across instances, $\hat\Delta-\Delta\sim(0,\ 2\sigma_n^2(1-\varrho))$, where $\varrho$ is the across-seed correlation of the two configs.
- **GPU or timing-based metrics.** Autoresearch (5-minute wall-clock budget) and MLAgentBench `speed_score` are noisy on re-run, and the incumbent's value is a stale draw.
- **Winner's curse.** `current_best` is a maximum of noisy draws, so it is biased above $J(c^{\text{inc}})$. Later true improvements are rejected more often, which pushes the campaign towards stagnation.

**Illustration.** Use the measured ResNet baseline seed s.d. $\sigma\approx0.0138$ AUC across 5 seeds, which includes split variation **[E plan/archive/Up-to-date.md:435-463]**, and *assume* $\varrho=0.5$, so that $\operatorname{sd}(\hat\Delta-\Delta)\approx0.0138$.

- A true gain of 0.005 AUC is discarded with probability $\Phi(-0.36)\approx0.36$.
- A true loss of 0.005 is kept with the same probability.
- Verify with $r$ paired fresh seeds lowers this to $\Phi(-0.36\sqrt{1+r})$: 0.30 at $r=1$ and 0.23 at $r=3$, at a cost of $r$ to $2r$ runs.

For scale, the Stage-1 net gain was 0.0076 **[E README.md:50-56]**, inside the baseline seed interval **[E plan/archive/master_plan.md:273-274]**. Verification is therefore expensive and only partly effective. When to spend it depends on $|\hat\Delta|/\sigma_n$ and on how much future search a false keep would misdirect, which is a function of remaining budget. That is a real control problem.

**[P] A noise-floor pilot is required.** Measure $\sigma_n$, and $\varrho$ for typical edits, per node. These numbers are not in the staged files for nodes other than ResNet. The OpenML $\sigma=0.0005$ in master_plan is a spread of best AUC across campaign seeds, not per-trial noise.

---

## 5. Estimands and what each training signal identifies

### 5.1 The ladder (Bellman objects from MDP:39-111)

- $Q^\rho_k(X,a)$: take $a$ at epoch $k$, then $\rho$. This is one-step deviation, equal to Paper A's $Y^g$ and $\mu_g$.
- $V^{\mathrm{L0}}(d)$: intervene once, at a randomly drawn eligible epoch. This is *exactly* identified from one-step branches **[E MDP:83-88]**.
- $V^{\pi}$: the deployed configurator acting at every epoch. **This is the primary estimand [P].**
- $V^*$: the sequential optimum.

The transfer bound

$$V^{\pi_d}-V^\rho\ \ge\ \sum_k\Big(\bar E_k(d)-\mathrm{sp}_k(d)\min\big\{1,\textstyle\sum_{s<k}\alpha^{\mathrm{eff}}_s\big\}\Big)$$

**[E MDP:93-105]** sums over 2-3 epochs per trial times $T=20$-$30$ trials here, about 40-90 epochs. With intervention rates that are not tiny, it is vacuous. So $V^\pi$ must be estimated by deployment. One-step certificates do not carry over.

### 5.2 Offline branched data (restore at $E_1$/$E_2$, branch every feasible $a$, $R$ continuations under $\rho$)

- **What it identifies.** The replay contrast $\tilde a_k(a)=\widetilde Q^\rho_k(a)-\widetilde Q^\rho_k(a_0)$ on the restored state $\widetilde X=T(X,\xi)$ **[E A/sections/06a_theory.tex:33-47]**.
- **What carries over to the intended contrast** under an unaudited-discrepancy allowance $p$, on the normalised outcome:
  - **contrast-only:** $|a-\tilde a|\le 2p$;
  - **sufficient for a positive sign:** $\tilde a>2p$, exact at $R=1$ for binary $S$;
  - **necessary at any depth:** $\tilde a>p/(1-p)$, and this also suffices when the discrepancy cannot track the replay contrast ($\Gamma=1$);
  - $\Gamma$ interpolates between the two **[E A/submission_sections/03b_measurements.tex:62-93, 103-110, 155-180]**.
  
  Sources of $p$ here: the unaudited node state, the ledger-derived `current_best`, and LLM provider drift (§2.2). Per Paper A, $p$ needs provenance: validated, structural, or a labelled sensitivity value **[E A/submission_sections/02_decision_estimands.tex:41-44]**.
- **[P] Cheap validation route.** Paper A's sufficient-evidence theorem has a paired-reference option: run a reference branch from a fresh reset plus a ledger replay **[E A/sections/06a_theory.tex:181-189]**. On CPU-deterministic nodes the restore can also be audited bit-exactly: same config and same seed must reproduce the metric.
- **Noise floor (separate from $p$).** Continuation outcomes are noisy (LLM sampling, $\omega$). Detecting $\tilde a$ needs $\tilde a\gg \operatorname{sd}(Y)/\sqrt{R\,n_{\text{epochs}}}$. Repetitions shrink this term. They never shrink $p$.
- **Labels.** Branching every feasible action gives **full-information labels** at each sampled epoch. Learning the one-step-greedy policy is then *cost-sensitive classification or regression on $Q^\rho$*. No bootstrapping is involved.
  - For a budgeted action such as verify, B's two-step continuation-value construction (Longstaff-Schwartz / fitted Q-evaluation with out-of-fold decisions) applies unchanged **[E B/docs/paper_split/B_CONTROLLER_DESIGN_20260927.md:§3]**.
- **What it cannot identify.** $V^\pi$ under repeated deployment, or $Q^*$. Fitted Q-iteration across epochs would bootstrap at post-intervention states that were never branched. That is the coverage gap in MDP L3 **[E MDP:111]**. Conservative offline RL needs a coverage assumption that this design does not test.
- **Data cost [P estimate].** Per root campaign: $K$ epochs $\times\,|A|\times R\times$ about $T/2$ continuation trials.
  - With $K=4$, $|A|=3$, $R=2$, $T=20$: about 240 trial-equivalents.
  - On OpenML that is about 1-2 CPU-hours per root, which is feasible for hundreds of roots.
  - On autoresearch it is about 20 GPU-hours per root, which is infeasible. Autoresearch is therefore deployment-only.
  - A truncated continuation horizon $h$ with an audited terminal value cuts cost but changes the estimand to $Q^\rho_h$. That must be declared (D7).

### 5.3 Online RL in real loops (GRPO-style)

- **Sampling.** Draw $G$ campaigns per instance under $\pi_\theta$ and use the group-relative terminal $Y$ as the advantage.
- **What it identifies.** $\nabla V^{\pi_\theta}$ directly. No restoration is involved, so **no $p$**, and history-dependent policies are allowed without a Markov assumption.
- **Costs:**
  - every sample is a full campaign;
  - credit is spread over about 40-90 epochs;
  - terminal noise comes from LLM sampling, $\omega$ and the audit;
  - only about 7 nodes exist, so instances within a node are dependent.
- **Feasible** only on CPU nodes and only after a warm start.

### 5.4 Hybrid (restore-anchored groups)

- **Method.** Restore at epoch $k$, branch $G$ continuations that each follow $\pi_\theta$, and form the group advantage at $k$. This is approximate policy iteration with fresh branching under the current policy $\pi_j$, not under $\rho$.
- **Trade-off.** Variance drops compared with §5.3. Each advantage carries Paper A's bias of at most $2p$, normalised, and the sign thresholds above apply per epoch.
- **Typical pipeline [P].** Supervised warm start (§5.2), then hybrid or online fine-tuning.

### 5.5 When RL is genuinely needed [P decision rule]

Full-information supervised learning on $Q^\rho$ is enough when the deployed policy rarely intervenes, or when interventions do not interact. This is measurable on development data:

- deviation budget $\sum\alpha^{\mathrm{eff}}$;
- on-support span $\mathrm{sp}$;
- the gap $V^{\pi_{\text{greedy}}}-V^{\mathrm{L0}}$ observed by deployment.

RL, or iterated policy improvement, is needed when:

- **actions have delayed or persistent effects:** stop, scope, memory, accept-worse;
- **budget is shared over time beyond two steps**, so spending now forecloses later. Two steps are handled by B's continuation-value rule;
- **greedy repeated deployment underperforms** its L0 prediction on held-out instances.

**[P]** Report the empirical ladder $V^\rho\le V^{\mathrm{L0}}\le V^{\pi_{\text{greedy}}}\le V^{\pi_{\text{RL}}}$. The paper's claim is *which rung the problem needs*, not that RL wins.

---

## 6. Arms, baselines, and the matched-budget protocol

**Arms [P]:**

1. **LLM self-control.**
   - At each epoch, a **side query** goes to the manager model on a *forked* context: the manager's prompt, the proposal or result, the masked action menu, and the remaining budget. It returns an action plus a scalar score per action, such as expected gain or P(decision changes).
   - The side query is never appended to the manager's context. The LangGraph manager is stateless, so there is no contamination.
   - Its scores pass through the shared spending rule (below) for the budget-matched version. Its *native* argmax under the budget cap is reported as descriptive.
   - Side-query tokens are charged to its cost.
   - Offline, the same side query run at branched states is scored against the full-information table with no new rollouts. This is B's tree-evaluation pattern.
2. **Trained configurator** (§8).
3. **Hybrid H1 (division of labour).** The configurator decides *whether and when* to intervene. The LLM decides *how*: it writes the revision content, or chooses among the masked actions once triggered.
4. **Hybrid H2 (LLM as advisor).** The LLM's side-query scores and its stated rationale are features in the configurator's input. The configurator decides. This tests whether the LLM adds information beyond $Z$.

**Baselines:**

- $\rho$ (never intervene);
- fixed schedules: always verify at keep; verify every $k$-th keep; always revise once;
- random intervention at matched realised budget;
- **harness heuristics**: skip when `repeated_bad` or `doom_loop` fires (`memory/similarity.py`, `manager/doom_loop.py`);
- a **noise-aware threshold**: keep iff $\hat\Delta>z\hat\sigma_n$, with $\hat\sigma_n$ from the pilot;
- for a8 only, classical multi-fidelity schedulers (successive halving / Hyperband; names are for the literature sweep, not claimed here);
- **hindsight oracle**, defined only on the one-step branch table: best action per sampled epoch given realised leaves, under budget. This is B's θ_OT with its headroom role **[E B/RUNBOOK.md:963-1001]**. A whole-campaign oracle is not available.

**Matched-budget protocol [P]:**

- Same instances $(n,\sigma)$, manager, $C$, LLM-call cap and $B_{\text{int}}$ for every arm.
- One **shared online spending rule** for all arms: spend on action $a$ iff $s_a>c_a$ and the remaining intervention budget exceeds a reserve $R_a(t)$. Each arm calibrates its own $(c,R)$ on development instances with the same tuning budget. This replaces B's batch allocator, since the coupling is now over time.
- $n_{\text{rep}}$ campaigns per instance per arm, because LLM sampling cannot be paired. Audit seeds are shared (common random numbers).
- **Primary contrasts:** configurator vs LLM self-control, and best hybrid vs both, on held-out instances.
- **Inference:** cluster bootstrap by instance, results by node, leave-one-node-out as descriptive.
- **Go/no-go:** a **headroom check** before any training. On the branch table, oracle minus best simple baseline must exceed the practical target.

---

## 7. Carry-over from Papers A and B

| Item | Fate [P] |
|---|---|
| Paired three-leaf trees | **Generalised**: per-epoch sibling sets over all feasible actions from one restored state. Verify-now / verify-later becomes a special case. |
| Original-root population | **Kept**: all epochs of all campaigns, including invalid trials, skipped proposals and stopped campaigns. No conditioning on a valid metric. |
| Shared allocator | **Adapted** to the shared online spending rule. The two-phase batch allocator is kept only for offline batch evaluation. |
| Cluster-by-family inference | **Kept** as cluster-by-instance. Node-level generalisation is explicitly limited by node count. |
| Paper A identification ($2p$, $p/(1-p)$, $\Gamma$, provenance of $p$) | **Kept** for training labels, $Q^\rho$ diagnostics and restore audits. Not applied to deployment contrasts, which involve no restore. |
| N1 / $m\le3$ tax | **Appendix**. Within a campaign one perturbed observation can change every later decision, so the analogue of $m$ is the whole remaining campaign. It is moot for deployment contrasts. |
| Continuation-value rule (Longstaff-Schwartz / FQE) | Kept as the two-step method for budgeted verify, and as a baseline learner. |
| DAC vocabulary, with the two deviations (budget coupling, minimal horizon) | Kept. The horizon is no longer minimal, so deviation 2 is restated. |
| Configurator scaffold (serialiser → frozen encoder → projection → ridge heads) | Becomes one architecture family (§8). Serialiser rules (allowlist, no post-decision events, prefix lineage) are kept. |
| D-HEADROOM | Kept as the go/no-go concept. |
| **Retired** | Candidate-consistency task and planted mechanism classes; 0.02 U target; 512-leaf cap and attempt-2 seal; Devstral executor binding; BAVAR as *primary* comparator (it may return as a VOI baseline); risk-ranked R-1 as stated (a risk-vs-advantage comparator could be rebuilt on $Z$). |

---

## 8. Configurator interface requirements (no architecture chosen)

- **Inputs:** $(Z_k,M_k,e)$ as in §3, optionally with the manager-visible text. The same information content must go to every learned or LLM arm (information parity, B's matching rule).
- **Outputs:**
  - a distribution over masked actions;
  - a **scalar score per action**, needed by the shared spending rule and the budget matching;
  - optional calibrated $\hat Q$ or advantage estimates;
  - for H1, a trigger only.
- **Latency:** at most about 1 s on CPU per call, because trials on CPU nodes take seconds. It must be negligible next to $\ell$.
- **Determinism:** deterministic given inputs and a seed. Every call is logged as a new `control_decision` event with input hash, output and version **[NEW]**, so the ledger stays complete.
- **Forbidden inputs:** audit or test metrics, sibling-branch outcomes, future records, other arms. It must not write the ledger. Decisions are committed by the control plane, which preserves the harness invariant that the control plane owns the decision **[E CLAUDE.md:113]**.
- **Generalisation unit:** held-out instances. Held-out nodes are optional.
- **Architecture families to discuss later:**
  - (i) tabular or GBM/ridge heads over hand-built ledger features;
  - (ii) frozen text encoder plus light heads (B's Kev/CLM slot);
  - (iii) a small LLM (about 1-4B) policy, SFT on full-information labels, then GRPO.

---

## 9. Open decisions

| ID | Question | Options | Recommendation |
|---|---|---|---|
| D1 | Budget unit | trial count (today) / worker runs or seconds plus LLM cap | Compute plus LLM cap. Without it, skip and stop are meaningless. |
| D2 | Terminal outcome | in-run `current_best` / audit at $K$ fresh seeds / held-out test | Audit at fresh seeds, plus test where it exists. Same seeds for every arm. |
| D3 | Core actions | §2.3 core / add scope (a6) now | Core = continue, skip, revise, verify(+demote). Stop if D1 = compute. a6 as the first extension. |
| D4 | Keep-rule invariant | frozen / configurator may override | Override only through verify's frozen response rule. No accept-worse in core. |
| D5 | Seed noise vs discrepancy $D$ (B's open R-4 item) | noise in $D$ / noise in kernel | GPU nondeterminism and fresh-seed variation are kernel noise. $D$ covers restore defects, ledger-derived state and provider drift. |
| D6 | Manager backend for branching | DeepSeek API / pinned local model | Pinned local model for branch data, which controls drift-type $D$. API only as a deployment check. |
| D7 | Continuation horizon for labels | full $T$ / truncated $h$ plus audited value | Truncated $h$ on development to start; declare $Q^\rho_h$. |
| D8 | Learning route | supervised only / staged / RL-first | Staged per §5.5. Report the ladder. |
| D9 | Remaining budget in configurator $Z$ | yes / no | Yes. This is a new object and leaves A's standing decision untouched. Needs author confirmation. |
| D10 | Instance pool | 6-7 existing nodes / add OpenML datasets | Add about 10-20 OpenML nodes. Each is YAML plus a node directory plus registry; small **[NEW]**. Hold out ResNet; autoresearch is deployment-only. |
| D11 | Primary estimand | $Q^\rho$ / $V^{\mathrm{L0}}$ / $V^\pi$ | $V^\pi$ at matched budget. $Q^\rho$ and L0 are secondary. |
| D12 | Use of the existing 1,355 trials (README:16) | evidence / development only | Development only: noise, features, invalid-trial predictors. The ledgers are not in the repo and contain no branches or counterfactual control labels. |
| D13 | Relation to B's sealed path | continue attempt 2 / shelve | Decide explicitly. The pivot replaces the task, the outcome and the targets. The 15/30 Nov cutoffs need re-dating. |

---

## Appendix A. Harness facts that bear on the design (verified in code)

1. **`prompt_manager` makes no LLM call.** It wraps the deterministic selector `select_bounded_objective` (`manager/prompt_manager.py:19`; `hyperparam_edits.py:446-553`). CLAUDE.md:141 calls it "LLM-backed". Only `langgraph_manager` calls an LLM. Arms that claim LLM behaviour must use it.
2. **`ClawWorker`'s non-deterministic path** writes `1 - val_bpb` under `node_spec.metric_name` (`claw_worker.py:277`). On autoresearch nodes (metric `val_bpb`, minimise) this would invert the sign if a trial took that path. The structured-edit path uses the node parser. Check the ledgers before reusing autoresearch data.
3. **`_current_best` on resume** ignores direction and includes metrics from invalid trials (`campaign.py:1043, 1136-1138`). See §2.2.
4. **Non-keep restore covers editable paths only** (`campaign.py:204-225, 715-716`). `LocalWorker` also restores on failure (`local_worker.py:199-201`).
5. **Trial counts:** LR 450, OpenML 460, MLAgentBench 50, ResNet 155, autoresearch 240, for a total of 1,355 (`plan/archive/master_plan.md:11-14, 32`). Instances number about 50 campaigns. This is the scale that rules out learning from the logs alone.
