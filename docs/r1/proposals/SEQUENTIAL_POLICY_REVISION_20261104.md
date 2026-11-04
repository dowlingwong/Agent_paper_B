# Paper B (R1) — revising the plan after the sequential-policy comment (proposal, 4 Nov 2026)

**Status.** AI-assisted proposal (Claude, chat session), written at the author's request on 4 Nov 2026. **Not adopted, authorizes nothing, changes no pin, STOP, rule or threshold, and is not evidence.** It becomes plan only through dated PLAN §10 rows that the author commits (draft rows in §9). The canonical PLAN, RUNBOOK and the three thread runbooks are revised from it afterwards (§10).

**Input.** `docs/r1/proposals/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md` (on branch `docs/runbooks-04nov`; cited below as "the comment", with its section numbers). Read against `mac-int-20261104` at `6ec83d8`, the Track S code on `trackS-ops-20261030`, and the documents listed in the 4 Nov brief.

**Companion.** Everything the comment proposes that does not fit Paper B — the Sequential Policy Track, the multi-step transition dataset, multi-step RL in the real loop and with the LLM decision model — is planned in `PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md`. This file only says what Paper B must do so that Paper C stays possible.

---

## 0. Summary

1. **The comment is right on the concepts and wrong on the scale for Paper B.** Its four-level claim ladder (dynamic control, future value, RL, decision model) and its demand to separate the C3 gate from Track S should be adopted now. Its Sequential Policy Track — behaviour-policy mixtures, repeated fork trees, offline and online multi-step RL — is a paper of its own and does not fit before 10 Jan 2027 next to the current critical path (B1 → B2 → X.7 → HK4–HK7 → B.7, with HoreKa 2 down 23 Nov – 4 Dec).
2. **Paper B keeps its shape:** C1 errors, C2 theory (one-step index theorem, reduction under (NF)+(NI), failure examples), C3 learned single-step belief under the rule, Track S as the campaign-level screen. What changes is **what Paper B claims** (§2), **how the documents describe RL and "dynamic"** (§3), **one dependency** (Track S no longer sits behind B.7), and **five cheap additions** (§4).
3. **The five additions** cost about 8–10 desktop days and about 1.5 % more Track S LLM calls; no new GPU budget:
   - W1/W2 — a transition-logging contract and a logging-only sidecar in every campaign runner, landed **before Track S S0.4 and sweep 2 (O6)**;
   - W3 — a budget dynamic-programming (stochastic-knapsack) baseline, as a Track S secondary and in the synthetic worlds;
   - W4 — synthetic positive controls for the channels Track S cannot calibrate (budget, information, incumbent interaction, feedback, strict null), which also carry the ≈ 15 Dec fallback;
   - W5 — the two offline checks of the reduction theorem that need no new labels (the (NI) masking test and the (NF-c) count).
4. **Paper B does not claim anything about multi-step RL (L3).** A7 (online RL) leaves Paper B. R-B is described as single-step, offline policy-gradient training with a verifiable reward.

---

## 1. Assessment of the comment, item by item

Disposition: **Adopt** (now, in Paper B) · **Adopt, scaled** (a smaller version in Paper B) · **Paper C** (moved) · **Already in plan** (state it more clearly).

| Comment § | Point | Disposition | Where in this proposal |
|---|---|---|---|
| intro, §1 | Split into L1 dynamic control, L2 future value, L3 RL, L4 decision model; partial results are publishable | **Adopt** | §2 |
| §2.1 | Track S answers only a restricted L1 (four pre-specified members, A2-U, verify off, two CPU nodes, binding W by design, one-way, only P2+ calibratable) | **Already in plan** (Track S rev 7.4 §0 says all of this); state it in the manuscript's limits | §2.3, §3.7 |
| §2.2 | Track P targets are single-step; `env.py` terminates after one step | **Adopt** (wording) | §3.4, §3.5 |
| §2.3 | C3 gate failure must not veto Track S, and a Track S null must not stop C3 | **Adopt** | §3.3 |
| §3.1 | Episode = whole campaign; Y = final incumbent's audited value; don't mix raw and normalised units | **Already in plan** for Track S (raw Y, PLAN:118 departure declared); state the cross-node rule | §3.7 |
| §3.2 | State contents; the trial-indexed `budget_frac_left` is not remaining budget; equal information across arms | **Adopt** | W2 (§4.2), §3.6 |
| §3.3 | First round E1 execute/skip with a frozen acceptance rule; E2 keep/verify later | **Paper C** (Paper B's Track S already varies both thresholds; the staged action space is a Paper C design) | Paper C §3 |
| §3.4 | Terminal reward Y_T − Y_0; shaping only as a training tool; don't add g in the main objective under a fixed budget | **Paper C**; for Paper B, Track S already uses terminal audited Y | — |
| §4.1 | Keep Track S's primary comparison, rules and pre-declaration | **Adopt** | §3.7 |
| §4.2 B1 | Budget DP / stochastic knapsack as a strong non-RL sequential baseline | **Adopt, scaled**: a Track S secondary (it was cut in rev 7: "the budget member replaces it"), plus a synthetic-world oracle | W3 |
| §4.2 B2 | Finite-horizon model-based rollout | **Paper C** | Paper C §6 |
| §4.3 | Myopic vs continuation-aware with the **same** immediate estimate | **Already in plan** as Track S's π′ (fork-learned, "one iteration of rollout-based approximate policy iteration", a secondary on 30 instances); name it as this contrast | §3.7 |
| §4.4 | Positive controls for budget, information, incumbent interaction, proposer feedback, strict null | **Adopt, scaled**: synthetic only, as sensitivity (not as a Track S gate) | W4 |
| §5 | Sequential Policy Track: transitions, behaviour mixtures, fork data, offline RL, online RL | **Paper C**, except the logging contract, which Paper B lands now | W1, W2; Paper C §§4–7 |
| §6.1 | Control-policy baselines (default, execute-all, random, tuned static, myopic noise-aware, A2-U, dynamic budget threshold, DP, MPC, racing, LLM self-control) | **Mostly in plan** (A0, prac-1/2, A1–A4, Track S static/dynamic, A2-U). DP added (W3). MPC → Paper C. Random at matched budget: add as a cheap D.3/Track S reference? → open item O3 | §4, §11 |
| §6.2 | Learning baselines: single-step SFT + rule, single-step action head, multi-step supervision, BC, DAgger, offline RL, online RL | Single-step ones **in plan** (R-A0, R-A1/2, Stage D). Multi-step supervision = π′ (**in plan**). BC, offline RL, online RL → **Paper C** | §2.2 |
| §6.3 | Architecture baselines (logistic/linear, LightGBM, MLP, no-text, plain LM, belief-only/action-only) | **In plan** (A3 LightGBM, TabPFN incl. information-matched, Qwen base control, context-only rung, R-A0 vs R-A1). MLP rung: open item O4 | §11 |
| §6.4 | Hindsight oracle and small-world DP oracle as diagnostics only | **In plan** (Track P §7.1 noisy-oracle ceiling); DP oracle added with W4 | W4 |
| §7 | Mechanism attribution (budget, information, feedback, interaction) | **In plan** as Track S S2, S3a channel contrasts (Δ_B, Δ_I, Δ_F), S4a, S1.1. Powered versions → **Paper C** | §3.7 |
| §8 | Layered matrix: synthetic → Track S CPU → harder tasks | Layers 1–2 **adopt**; layer 3 (powered multi-step on GPU tasks) → **Paper C** | §2.3 |
| §9 | Campaign as the unit; train/dev/test isolation; primary comparisons and multiplicity; no copying n = 300; training seeds | **Adopt** for every addition | §5 |
| §10 | Cost reporting incl. development cost | **Adopt** for D.3 and Track S reporting | §6 |
| §11 | Risk table | Paper-B-relevant rows folded into §7 | §7 |
| §12 | Order: concepts → state/action/data contract → Track S as approved → strong non-RL baselines → small-model RL → LLM multi-step RL | Steps 1–4 **adopt** (Paper B); steps 5–6 → **Paper C** | §4, Paper C |

**One thing the comment does not say, and Paper B should.** The manuscript draft (`papers/r1/sections/problem.tex`) calls per-proposal, forecast-driven configuration "dynamic". Under the reduction theorem that is a contextual bandit, not sequential control. The word has to be split (§3.2), or every reviewer who reads the comment's L1 will find the paper using "dynamic" for two different things.

---

## 2. What Paper B claims after the revision

### 2.1 The claim ladder

| Level | Question | What Paper B provides | What it does **not** claim |
|---|---|---|---|
| **L0 (new name for C1–C2)** | Does noise make the default loop err, and what is the optimal one-step rule? | C1 measured errors; C2 one-step index theorem (Prop 8′ in the revision draft), the winner's-curse result, the reduction theorem under (NF)+(NI), and the two unbounded-loss failure examples | Global optimality outside (NF)+(NI), or under a hard budget |
| **L1 dynamic (sequential) control** | Does a state-dependent threshold beat a tuned static one on whole campaigns? | Track S, one-way screen, on the declared nodes; the matched-static guard; synthetic sensitivity (W4) | Absence of sequential value from a Track S null; anything about the four-member family beyond π\* |
| **L2 future value** | With the same immediate estimate, does adding a continuation term help? | Descriptive only: Track S π′ (secondary) and the budget-DP secondary (W3); S3a channel contrasts; W4 oracle gaps in synthetic worlds | A powered L2 result (Paper C) |
| **L3 RL** | Does multi-step RL beat strong non-RL sequential methods? | Nothing | Any L3 statement. R-B is single-step policy-gradient training |
| **L4 decision model (single-step)** | Does a model that reads the proposal beat structured forecasters, at equal information? | C3 ladder (A3, TabPFN incl. information-matched, Qwen control, Kev, A4 self-control), aggregate gate, leave-one-suite-out, D.3 closed loop | Multi-step decision-model value (Paper C) |

### 2.2 Which method sits at which level

| Method in the plan | Level | Correct description |
|---|---|---|
| A1–A3, A5 + rule (R-A0) | L4 (single-step) | Learned prior under the one-step rule |
| R-A1/R-A2 action head | L4 (single-step) | Decision-focused fine-tuning (cost-sensitive classification) |
| R-B (optional) | L4 (single-step) | Single-step, offline policy-gradient training (GRPO-style) with a verifiable reward; a contextual-bandit RL arm. Not multi-step RL |
| Stage D (one DAgger round, 1–2 T1 nodes) | L4 | On-policy state aggregation; evidence of state-distribution shift, not of a policy-value gap (R1-WORDING-30OCT) |
| Track S static/dynamic families | L1 | Tuned static vs tuned state-dependent thresholds |
| Track S π′ | L2 (descriptive) | Multi-step supervised regression on fork outcomes, then a frozen rule |
| Budget DP (W3, new) | L1/L2 (descriptive) | Non-RL sequential baseline for the budget channel |
| A7 online RL | — | **Leaves Paper B** (Paper C) |

### 2.3 Revised contributions (PLAN §3 box, proposed wording)

> **C1** — measured control errors and wasted runs (unchanged).
> **C2** — theory: the one-step index theorem; the reduction of the loop to independent one-step (contextual-bandit) decisions under no feedback and no information at a fixed run price; unbounded-loss examples when either condition fails; the hard-budget case as a declared non-theorem. The reduction's offline testable implications are checked (W5).
> **C3** — a learned single-step belief under the C2 rule: does it close the gap to the noisy oracle beyond the index policy, structured forecasters and LLM self-control, at equal information (L4)?
> **Sequentiality screen (Track S)** — does a tuned state-dependent policy beat the tuned static rule on whole campaigns (L1, one-way)? Descriptive L2 evidence from π′, the budget-DP secondary and the fork channel contrasts. Synthetic controls state the screen's sensitivity per channel.
> **C4 (secondary, appendix)** — the decision-independence diagnostic on forced keep/discard pairs, descriptive. The debiased-memory A/B and any online RL move to Paper C.
> **Not claimed:** the value of multi-step RL, or of multi-step training of the decision model.

This keeps the novelty position the author set on 23 Oct (the self-control vs trained vs hybrid comparison) and answers the worry that "DAC + RL-trained configurator" alone is thin: the DAC contribution is the **reduction result plus a measured screen**, not an RL claim.

---

## 3. Revisions, document by document — what and how

Each item names the file, the problem, and the replacement. "Row" means a PLAN §10 draft row in §9. The editor follows the 4 Nov routing (§10).

### 3.1 PLAN §2–§3 (the question and the contributions)

- **Problem.** §2 still lists "How much does learning add?" with RL implicit; the §3 box says "C4 also decides whether online RL (A7) is warranted".
- **How.** Insert the §2.1 ladder after §2's question as "Claim levels (4 Nov revision)". Replace the §3 box by the §2.3 wording. Delete the A7 sentence from C4. Row **R1-SEQ-CLAIMS**.

### 3.2 Vocabulary: "contextual" vs "sequential" configuration

- **Problem.** `papers/r1/sections/problem.tex` names three levels — static, per-instance, dynamic — and defines "dynamic" as per-proposal, forecast-driven. Track S's "dynamic" means state-dependent (budget, history). The comment's L1 uses the Track S meaning.
- **How.** Four levels everywhere (manuscript, PLAN, TECH_ROUTE, C3_DESIGN, Track S design §0):

  | Level | Definition | Where |
  |---|---|---|
  | static | one configuration for every instance and trial | A0, prac-1, Track S `static` |
  | per-instance | set once per instance (fitted or predicted from descriptors) | context-only rung |
  | **contextual** | per proposal, a function of the proposal and the current information through a one-step rule; optimal under (NF)+(NI) at a fixed price | A1–A6 |
  | **sequential** | depends on the state beyond the current proposal's one-step value (remaining budget, uncertainty, history) | Track S `dynamic`, π′, budget DP |

  The manuscript sentence becomes: *"In DAC terms, contextual configuration is the case in which the DAC problem has reduced to a contextual bandit (Theorem 1); sequential configuration is needed only where the reduction fails."* Row **R1-SEQ-VOCAB**.

### 3.3 The C3 gate and Track S become parallel branches

- **Problem.** In the 18 Oct design the only sequential measurement (the online pilot and A7) sat behind the one-step gate (Track S design §0), and TECH_ROUTE's dependency graph still has no Track S chain at all, so a reader takes the gate as the entry to every sequential question. T4 revision R4 already says the gate's scaled one-step gain has no guaranteed sign relation to the campaign gain outside (NF)+(NI).
- **How.** State in RUNBOOK (Phase B, Track S, §6) and TECH_ROUTE:
  - B.7 failing does not stop or reweight Track S; Track S's outcome does not change B.7 or Phase C.
  - Phase C still requires B.7 (unchanged).
  - Neither outcome authorizes Paper C work.
  - Track S keeps its own STOPs, its host priorities (Track X on TASL-2, Track P on TASL-7) and its ≈ 15 Dec fallback.
  - In TECH_ROUTE's mermaid graph, Track S is a separate chain from host preparation to "manuscript claims", with no edge from the gate.
- This changes no execution today: Track S has never actually waited for B.7 in the current runbooks. It removes the logical dependency from the documents and from the manuscript's argument. Row **R1-SEQ-GATES-PARALLEL**.

### 3.4 RL wording in Track P, C3_DESIGN and RUNBOOK

| File and place | Current text (gist) | Replacement |
|---|---|---|
| `TRACK_P_POST_TRAINING.md` §1, positioning note | "Stage D (DAgger) is the empirical evidence for (b)" | "Stage D measures state-distribution shift under the deployed configurator; it is not evidence of a policy-value gap or of sequential value (R1-WORDING-30OCT). Whether the full loop needs sequential control is Track S's question (L1)." |
| same, §1 table, "Action" row | "skip / execute; after execution keep / reject" | add: "Track P trains single-step targets only; the offline environment terminates after one step." |
| same, §6.4 heading text | "reasoning arm (GRPO)" | add one sentence: "R-B is single-step, offline policy-gradient training against a verifiable per-proposal reward; it is the only arm the paper calls RL, and it makes no multi-step claim." |
| `C3_DESIGN.md` §2 point 5 | per-proposal reward is "valid under DI, T4 Proposition 10" | "The per-proposal reward is the one-step objective of the index theorem (revision Prop 8′) and needs no independence condition. Its sum equals the campaign objective only under (NF) and (NI) (reduction theorem); otherwise it is a declared one-step quantity (T4 revision R3, R4)." |
| `C3_DESIGN.md` §5, row (A7) | "stage 3 online RL, only if the DI test shows a material violation" | "(A7) moved to Paper C (R1-SEQ-A7-MOVE). A DI violation is necessary, not sufficient, for any non-myopic gain (reduction theorem, contrapositive)." |
| `C3_DESIGN.md` §5 "Stage 2, precisely" | still describes the old 12-bin action and greedy-bin deployment | mark as superseded history (already superseded by R1-C3-POST; add a pointer so no reader takes it as the current design) |
| `RUNBOOK.md` §6 row "DI strongly violated (C4)" | "One-step offline values are biased; A7 (online RL) becomes justified, with T4 Proposition 10(b)" | "Report it with the reduction theorem's contrapositive: a violation is necessary, not sufficient, for a non-myopic gain. Offline one-step values are then declared quantities, not campaign estimates. Online RL is Paper C." |
| `r1/c3/env.py` docstring | "Offline contextual-bandit environment" | no code change; add one docstring line: "one-step by design (Track H.8); not a model of the campaign." R1-H8-DEFERRED stands; the execute/skip amendment is needed only by Paper C |

Row **R1-SEQ-RL-WORDING** (Track P, C3_DESIGN, RUNBOOK, env docstring) and **R1-SEQ-A7-MOVE**.

### 3.5 Theory documents

- **Problem.** `theory/T4_FEEDBACK_PROPOSER.md` still carries the old Prop 10(a) and its §6 "Reading" (RL-necessity claims). The manuscript already uses the revised statements.
- **How.** No change before the author's proof check (R1-T4-DI-FIX). Add a one-line pointer at the top of T4 §6: "superseded in the manuscript by the revision draft; see `proposals/T4_PROP10_REVISION_20261028.md` §3 contrapositive and R5." The open items of R1-T4-DI-FIX stay with the author: R1 (incumbent-error model), R4 (does the gate's "20" count proposals or executed runs), and which §6 tests enter the plan — this proposal recommends two of them (W5).

### 3.6 Budget fields in features and logs

- **Problem.** The C3 feature `budget_frac_left` (`r1/c3/features.py`:98, 385) is `1 − (b − 1)/runs_total`, indexed by trial, not by worker runs. Track S already uses `worker_runs_remaining` (design §1 H7).
- **How.**
  - **Do not change the C3 feature set** before B.3. In training (execute-all sweeps) and in deployment it is computed the same way from the trial index, so there is no train/deploy mismatch. Rename it in the documents to "trial fraction left" and never use it as remaining budget in any sequential analysis.
  - **Log the real budget** in every campaign record (W2): worker runs used and left, LLM calls used and left, proposal slots left, the Track S `r`.
  - Row **R1-SEQ-BUDGET-FIELDS**.

### 3.7 Track S design (rev 7.4 → a short rev 8, documents and logging only)

Track S's primary comparison, families, n = 300, Holm rule, placebos, decision routes and pins for S0.1 stay **unchanged**. Rev 8 adds, as declared secondaries or logging, before S0.8 (the pre-declaration) and preferably before S0.4:

1. **§0 framing.** One paragraph mapping Track S to the ladder: primary = L1 screen; π′, the budget-DP secondary and the S3a contrasts = descriptive L2; nothing about L3. Name π′ as the comment's controlled "myopic vs continuation-aware" contrast (it uses the same A2-U forecast plus a fitted continuation term, comment §4.3).
2. **Budget-DP secondary (W3).** Re-introduce the DP candidate that rev 7 cut, **as a secondary only**, on the existing 30-instance secondary subset of S3e, fitted on m\*'s S0.7 dev decisions. It cannot move the route.
3. **Transition sidecar (W2).** A logging-only extension of `RootRecord.decisions` and `LeafRecord`, with a test that ledgers and decisions are byte-identical to pin `d10b05b7`.
4. **Synthetic sensitivity (W4).** New worlds reported next to S0.6's controls as "additional sensitivity, not a Track S gate"; S0.6's STOP rule and its calibrated controls are unchanged.
5. **Cross-node unit rule.** Per-node primary in raw audited Y (as now); any cross-node summary uses Y/σ_node with σ_node declared before S3e; raw units are never averaged.
6. **Manuscript limits list** (copied from design §0 and comment §2.1): four pre-specified members, A2-U is a model-based Bayes-myopic controller and not the deployed C3 rule, verify off, two CPU nodes plus the GPU extension outside the decision, W chosen to bind, one-way, only P2+ (keep feedback) and P1-diffuse (information) calibratable.

**Timing.** The S0.1 re-run (O3 step 2) uses no collector changes and proceeds. Rev 8's code (items 2–3) needs one independent review and a new pin before S0.4. If it is not ready when S0.4 is due, S0.4–S0.7 run on `d10b05b7` and transitions for those phases are exported later from roots, leaves and harness ledgers with the gaps listed (W1). Rev 8 must be committed before S0.8 in any case, or the additions become post-hoc and are reported as exploratory. Row **R1-SEQ-TRACKS-REV8**.

### 3.8 Manuscript (`papers/r1/`)

| Section | Change |
|---|---|
| `problem.tex`, DAC paragraph | four levels (§3.2); "contextual configuration is the reduced case" sentence |
| `theory.tex`, "Scope" | add: "Under a hard budget the problem contains a stochastic-knapsack component; Track S's budget member and the budget-DP secondary probe it empirically." |
| `theory.tex`, "Consequences" | add the claim ladder in two sentences: the theorem says where sequential control can help; Track S screens for it; nothing here concerns which learning method would exploit it |
| `setup.tex`, offline gate | replace the "≥ 2 nodes" criterion by R1-BX-D8 (aggregate) once R1-BX-D8-CONFIRM exists (already pending, M11/M8) |
| new results structure | results ordered by level: L0 (errors, theory checks incl. W5), L4 (C3 ladder, gate, transfer, D.3), L1/L2 (Track S, synthetic sensitivity) |
| `limitations.tex` | Track S limits (§3.7 item 6); single-step training only; no multi-step RL; offline evaluation of skipping is optimistic for Bayes-myopic controllers under (NF) (T4 revision R6) |
| future work (one paragraph) | "multi-step policies and their learning are studied separately", with no promised results |

---

## 4. New work items for Paper B

### 4.1 W1 — transition-logging contract (desktop; 1–1.5 days)

- **What.** A short spec `docs/r1/TRANSITIONS_SPEC.md` (proposed name) defining one record per decision point, so that every campaign Paper B runs is reusable as multi-step data later. Fields (full schema in Paper C plan §4):
  - identity: node, instance, campaign, root/fork ids, step index, epoch (E1/E2), policy string and version, action, **action probability** (1.0 for deterministic policies, else the logged probability), seed key and repetition;
  - state before the decision: proposal hash and diff/edit summary, incumbent configuration hash, duplicate/no-op flags, the controller's forecast (π, μ, τ, σ, V̂\*, m̂), worker runs used/left, LLM calls used/left, proposal slots left, keeps and skips so far;
  - outcome: observed Δ̂ if executed, kept or not, next incumbent hash;
  - episode end: `terminated` (W or LLM cap exhausted by protocol) vs `truncated` (crash, timeout, pre-emption, parse failure beyond retry), with the reason;
  - terminal: Y_terminal and its audit seeds (on the last record of the campaign).
- **First step.** List what the harness ledger, the C3 sweep rows and Track S's `RootRecord`/`LeafRecord` already hold. From the Track S schema: per-trial `decisions` (index, epoch, action, index value, eligible) exist; per-step budget, the full forecast tuple and incumbent hashes do not. The spec should be met by **derivation from existing records plus a small sidecar**, never by changing what a controller sees.
- **Owner.** Chat session (desktop, CPU); review by a fresh agent.

### 4.2 W2 — logging-only sidecar in the campaign runners (desktop; 1–2 days + review)

- **Where.** (a) the C3 sweep runner used by sweep 2 T0 (O6, Mac M4) and by the HoreKa T1 sweep (HK6); (b) the Track S collector (rev 8); (c) the D.3 closed-loop runner (M15/O11).
- **Rule.** Logging only. Acceptance test per runner: on a fixed-seed fixture, decisions, ledgers and artifacts are byte-identical with and without the sidecar.
- **Deadline.** Before O6 starts (sweep 2 T0, after X.7, ≈ mid-Nov) and before Track S S0.4. For HK6, before the HoreKa submission freeze on 20 Nov 12:00 if HK6 code is pinned before then; otherwise at the next pin.
- **Behaviour policies, for the record.** Sweep 2 is execute-all (every non-rule proposal is executed): it gives transitions under one policy with no skip coverage. Track S S0.4 (execute-all), S0.5 (A2-U at two prices), S0.7 (15 static + 4 dynamic configurations), S3a (forks) and S3e (π\*, m\*, matched static, secondaries) together form a natural behaviour mixture. Paper B adds **no** exploratory campaigns for coverage; that is Paper C's.

### 4.3 W3 — budget-DP baseline (desktop; about 2 days)

- **What.** A stochastic-knapsack execute rule: execute iff the current proposal's one-step value V̂\*_n exceeds the estimated marginal value of keeping one run, given runs left and proposal slots left. The marginal value is computed by backward induction over (runs left, slots left) with V̂\* drawn i.i.d. from its empirical distribution over m\*'s S0.7 dev decisions (per node; no new dev campaigns), and the keep rule unchanged (A2-U margin).
- **Interpretation limit (comment §4.2).** The i.i.d. future-value model ignores dependence on the incumbent and the history; it is a model-based heuristic, not an optimal policy, and it is described that way.
- **Uses.** (i) A Track S secondary on the existing 30-instance subset (rev 8); (ii) in the synthetic worlds of W4, where the exact DP optimum is also computable and gives the oracle gap; (iii) offline, a descriptive replay on sweep-2 T0 ledgers truncated at W (the same truncation rule as Track S S0.5b).
- **Cost.** About +30 campaigns per Track S node, ≈ 1.2k LLM calls (≈ 1.5 % of the ≤ 79k planned).

### 4.4 W4 — synthetic sensitivity worlds (desktop CPU; 2–3 days)

- **Worlds** (comment §4.4), all with a scripted manager and in-process worker, as in S0.6:
  1. budget opportunity cost (a small sure gain now consumes a run needed for a later large gain);
  2. information value (the T4 revision's Prop 10(c) world, with a probe and a correlated later edit);
  3. incumbent interaction (B is valuable only after A is kept, or A blocks B);
  4. proposer feedback (keeps shift the next proposal law; the existing P2+ is one instance);
  5. strict null (no channel; the myopic rule is optimal).
- **Per world, report:** the exact DP-optimal value where the state space allows, the value of the best static rule, of each Track S member, of π′ and of the budget DP; the detection power of the Track S pipeline at Track S's n; P(correct member); the false-positive rate on the null.
- **Status.** Pipeline and sensitivity evidence only, never evidence about the real loop. It also fills the content of R1-BX-D10's fallback ("theorem plus synthetic controls") if Track S has no campaign-level result by ≈ 15 Dec.
- **Constraint.** Worlds and their effect sizes are fixed and committed before Track S S3e outcomes are read, and are not tuned afterwards.

### 4.5 W5 — offline checks of the reduction theorem (desktop; about 1 day after labels)

From the T4 revision §6, the two checks that need no new runs:
- **(NI) masking test.** The C3 forecaster (A3, and A5 if available) trained with vs without executed results in its history features, both given the same proposal history, compared out of sample on RPS and decision utility (sweep 2 T0, and T1 where labelled). An improvement beyond estimation error is evidence against (NI); its absence does not establish (NI).
- **(NF-c) count.** In sweep campaigns, the share of later proposals whose duplicate status depends on an earlier execution (re-proposals of configurations a skip would have left unevaluated).
- **Owner.** M14 (B.3 offline arms), after R1-BX-D8-CONFIRM. Row **R1-SEQ-THEOREM-CHECKS** (also resolves one of R1-T4-DI-FIX's open items).

### 4.6 What Paper B does not add

- No exploratory (ε-random) campaigns, no repeated fork trees, no transition model, no MPC, no behaviour cloning, no offline or online multi-step RL, no multi-step training of any decision model. All are in the Paper C plan.
- No new arm in D.3. The budget-DP rule stays in Track S and the synthetic worlds; D.3 already carries many arms (open item O5).

---

## 5. Statistical rules for the additions

- **Unit.** The campaign instance; paired differences within an instance (comment §9.1). Trials inside a campaign are never independent units.
- **Primary comparisons are unchanged:** Track S's π\* vs m\* (Holm, one-way) and the C3 aggregate gate (R1-BX-D8). Every addition is a declared secondary or descriptive quantity; none uses Track S's Holm budget or can move a route.
- **Isolation.** The budget-DP rule has no free coefficient to tune: its future-value distribution is fitted on m\*'s S0.7 dev decisions, which already exist, and it is evaluated only on the S3e secondary subset. It needs no new dev campaigns and touches no S3e outcome before it is frozen. Synthetic worlds use their own RNG seeds. The masking test uses the C3 train/validation/test partitions as declared for B.3.
- **Seed blocks.** Paper B reserves no new instance-seed blocks except the DP dev instances above. The 7001–7005 / 7006–7010 audit rule keeps its present use. Paper C reserves its own blocks (Paper C plan §11).
- **Sample sizes.** No addition is powered. They are reported with intervals and as descriptive.

---

## 6. Cost and schedule

| Item | Owner | Effort | Server cost | Must be done by |
|---|---|---|---|---|
| Document and wording revisions (§3.1–§3.6) | chat session | 1 day | none | before the next runbook revision |
| Manuscript changes (§3.8) | chat session | 1 day (parallel to writing from early Dec) | none | Dec |
| W1 transition spec | chat session | 1–1.5 days | none | ≈ 10 Nov |
| W2 sidecar (C3 sweep runner, Track S collector, D.3 runner) + review | Mac-local (M4, M6 scope) or chat session | 1–2 days + review | none | before O6 and Track S S0.4 (≈ mid-Nov) |
| W3 budget DP + tests | chat session | ≈ 2 days | ≈ 1.2k LLM calls per Track S node | before Track S S0.8 |
| W4 synthetic worlds | chat session | 2–3 days CPU | none | before Track S S3e outcomes; report by 8 Dec |
| W5 masking test, (NF-c) count | Mac-local M14 | ≈ 1 day | none | with B.3 (after labels and R1-BX-D8-CONFIRM) |
| Track S rev 8 document + review | chat session | ½ day + review | none | before S0.4 (preferred), S0.8 (latest) |

Total ≈ 8–10 desktop days, spread so that only W1/W2 sit near the critical path. The Mac-local agent's critical-path items (M2, M3, M10, M11) keep priority; following the author's 28 Oct preference, documents, W1, W3 and W4 go to the chat session. The dates of R1-BX-D14 are not changed by this proposal.

---

## 7. Risks specific to this revision

| Risk | Consequence | Mitigation |
|---|---|---|
| The sidecar changes behaviour | Track S pairing or sweep comparability breaks | Byte-identical-ledger test per runner; review; new pin recorded |
| W2 misses O6 or S0.4 | Some campaigns lack per-step budget/forecast fields | Derive from ledgers afterwards; list the gaps; never re-run for logging alone |
| Adding secondaries after seeing Track S data | Post-hoc analysis | Commit rev 8 before S0.8; otherwise label as exploratory |
| Synthetic worlds built to favour a method | Circular sensitivity claims | Worlds and effect sizes fixed before S3e; include the strict null; report all methods in all worlds |
| Desktop capacity | Critical-path Mac items slip | Chat session takes W1, W3, W4, documents; Mac-local takes only W2 and W5 inside existing M4/M6/M14 scope |
| Reviewers still read "DAC" as "needs RL" | Novelty attacked from the RL side | §3.2 vocabulary; claim ladder; explicit "not claimed" line |

---

## 8. Effects on the three threads

| Thread | Change |
|---|---|
| **Mac-local** | M4: add the W2 sidecar to the sweep-2 runner (byte-identical test). M6: Track S rev 8 code parts (DP secondary, collector sidecar) if routed there; otherwise review only. M8: manuscript changes §3.8. M14: W5. M15: D.3 runner sidecar. No change to M2, M3, M10, M11 or their order. |
| **Operator** | O3: unchanged through the S0.1 re-run; S0.4 waits for the rev-8 pin only if the author chooses the "preferred" timing (§3.7), otherwise proceeds on `d10b05b7`. O6: runs with the sidecar pin. O11: D.3 runner with the sidecar. No new runs. |
| **HoreKa** | HK6/HK7: the T1 sweep runner carries the sidecar if its pin is cut after W2; otherwise transitions are derived later. No new jobs and no budget change. |

---

## 9. Draft PLAN §10 rows (for the author)

```
| R1-SEQ-CLAIMS (date) | Paper B's claims follow the four-level ladder of `proposals/SEQUENTIAL_POLICY_REVISION_20261104.md` §2: C1–C2 (errors, one-step and reduction theory), L4 single-step (C3), L1 sequential control (Track S, one-way screen), L2 descriptive only (π′, budget-DP secondary, fork contrasts, synthetic oracle gaps). Paper B makes no claim about multi-step RL (L3) or multi-step training of the decision model. PLAN §3's box is replaced by §2.3 of that proposal. |
| R1-SEQ-VOCAB (date) | Configuration levels are static, per-instance, contextual (per-proposal through the one-step rule; the reduced DAC case) and sequential (state-dependent beyond the proposal). "Dynamic" is used only for Track S's state-dependent family. Applies to the manuscript, PLAN, TECH_ROUTE, C3_DESIGN and the Track S design. |
| R1-SEQ-GATES-PARALLEL (date) | The C3 gate (B.7) and Track S are parallel branches: B.7's outcome does not stop or change Track S, and Track S's outcome does not change B.7 or Phase C. Phase C still requires B.7. Neither outcome authorizes Paper C work. TECH_ROUTE's graph is redrawn accordingly. |
| R1-SEQ-RL-WORDING (date) | Wording: R-B is single-step, offline policy-gradient training with a verifiable per-proposal reward and the only arm called RL; Track P and the offline environment are single-step by design; Stage D measures state-distribution shift only. TRACK_P §1 and §6.4, C3_DESIGN §2 (point 5) and §5, RUNBOOK §6 (DI row) and the `r1/c3/env.py` docstring are corrected as in the proposal §3.4. |
| R1-SEQ-A7-MOVE (date) | A7 (online RL) and the C4 debiased-memory A/B leave Paper B for the follow-up paper; C4 in Paper B is the descriptive DI diagnostic only. A DI violation is reported with the reduction theorem's contrapositive (necessary, not sufficient). |
| R1-SEQ-BUDGET-FIELDS (date) | The C3 feature `budget_frac_left` stays as defined (trial-indexed) and is described as "trial fraction left"; it is never used as remaining budget. Every campaign record logs worker runs used/left, LLM calls used/left and proposal slots left. |
| R1-SEQ-TRANSITIONS (date) | Transition-logging contract `docs/r1/TRANSITIONS_SPEC.md` <sha> is adopted. The C3 sweep runner (sweep 2 T0 and T1), the Track S collector and the D.3 runner carry a logging-only sidecar, each with a byte-identical-ledger test and an independent review, pinned before O6 and Track S S0.4 where possible; campaigns run before a pin are exported later from their records with the gaps listed. |
| R1-SEQ-TRACKS-REV8 (date) | Track S design rev 8 (documents and logging; primary comparison, families, n, Holm rule, placebos and S0.1 pins unchanged): ladder framing; π′ named as the myopic vs continuation-aware contrast; a budget-DP secondary on the 30-instance secondary subset, fitted on m*'s S0.7 dev decisions; the transition sidecar; additional synthetic worlds as sensitivity only; per-node raw Y with σ_node-scaled cross-node summaries. Committed before S0.8; preferred before S0.4. |
| R1-SEQ-SYNTH (date) | Synthetic sensitivity worlds (budget, information, incumbent interaction, proposer feedback, strict null) with exact DP oracles where computable, fixed before any Track S S3e outcome; reported as pipeline sensitivity only and used for R1-BX-D10's fallback. |
| R1-SEQ-THEOREM-CHECKS (date) | Two offline checks of the reduction theorem enter B.3 (M14): the (NI) masking test and the (NF-c) count, as specified in `proposals/T4_PROP10_REVISION_20261028.md` §6. Resolves that open item of R1-T4-DI-FIX for these two checks. |
| R1-SEQ-PAPER-C (date) | The Sequential Policy Track, multi-step transition collection beyond logging, model-based rollout/MPC, behaviour cloning, offline and online multi-step RL, and multi-step RL of the decision model are scoped to the follow-up paper (`proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md`); no Paper B resources are allocated to them. |
```

---

## 10. Order of edits after adoption

1. Author commits the rows he adopts (§9).
2. Chat session: §3.1–§3.6 document edits on one branch; W1 spec; Track S rev 8 document. Independent review of each.
3. Mac-local: W2 in M4 (sweep runner) and the Track S collector; the author commits the pins.
4. Chat session: W3, W4 (CPU), with tests and review.
5. Operator/HoreKa runbooks: a short revision noting the sidecar pins and Track S rev 8 (no new steps beyond that).
6. Manuscript (§3.8) as writing proceeds; W5 with B.3.

---

## 11. Open questions for the author

| # | Question | Options | Recommendation |
|---|---|---|---|
| O1 | Track S rev 8 timing | (a) before S0.4 (delays S0.4 by the review, a few days); (b) S0.4–S0.7 on `d10b05b7`, rev 8 from S3a/S3e on | (a) if the S0.1 re-run passes before W2 is reviewed; else (b) |
| O2 | Who implements W2 in the Track S collector | Mac-local (M6) or chat session with Mac-local review | chat session implements, Mac-local reviews (M6 is "on demand") |
| O3 | A random matched-budget reference arm (comment §6.1) | add to Track S secondaries; add to D.3; neither | neither: the floor is already covered by A0 and execute-all, and it costs campaigns |
| O4 | A small MLP rung in the C3 ladder (comment §6.3) | add next to A3/TabPFN; skip | add only if M11 has capacity; it is cheap offline |
| O5 | Budget DP in D.3 | add as an arm; Track S and synthetic only | Track S and synthetic only |
| O6 | Where C4's debiased-memory A/B goes | Paper B appendix (current "or later"); Paper C | Paper C (R1-SEQ-A7-MOVE) |
| O7 | Working name of the follow-up paper | "Paper C"; other | the author's choice |

## 12. What this proposal does not do

It does not change Track S's primary design, any C3 gate number, any authorization, host assignment, budget or date; it does not start any run; and it does not adopt any theory claim before the author's proof check.
