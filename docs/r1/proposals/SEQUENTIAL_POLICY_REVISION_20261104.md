# Paper B (R1) — revising the plan after the sequential-policy comment (proposal, revision 2, 5 Nov 2026)

**Status.** AI-assisted proposal (Claude, chat session), written at the author's request on 4 Nov 2026 and revised on 5 Nov 2026. **Not adopted, authorizes nothing, changes no pin, STOP, rule or threshold, and is not evidence.** It becomes plan only through dated PLAN §10 rows that the author commits (draft rows in §9). The canonical PLAN, RUNBOOK and the three thread runbooks are revised from it afterwards (§10).

**Input.** `docs/r1/proposals/REVIEW_COMMENT_SEQUENTIAL_POLICY_20261104.md` (on branch `docs/runbooks-04nov`; cited below as "the comment", with its section numbers). Read against `mac-int-20261104` at `6ec83d8`, the Track S code on `trackS-ops-20261030` (`f5d5c6b`, descending from the pin `d10b05b7`), and the documents listed in the 4 Nov brief.

**Companion.** Everything the comment proposes that does not fit Paper B — the Sequential Policy Track, the multi-step transition dataset, multi-step RL in the real loop and with the LLM decision model — is planned in `PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md`. This file only says what Paper B must do so that Paper C stays possible.

### Revision 2 (5 Nov 2026) — what changed and why

Revision 1 (commit `5b3b714`) was reviewed independently: `docs/r1/reviews/SEQUENTIAL_POLICY_REVISION_REVIEW_20261104.md`, verdict **REVISE** (0 BLOCKING · 12 MAJOR · 21 MINOR). In chat on 5 Nov the author also agreed with three recommendations. These are reflected below but **are not decisions until the matching rows are committed**:

- (a) amend R1-TRACKS-FRAMING so that Track S outcomes no longer govern Paper B's RL arms (§3.3, row R1-SEQ-TRACKS-FRAMING-AMEND);
- (b) replace the logging sidecar in the sweep runner and the Track S collector with an archive plus an offline exporter, with no Track S pin change and no change to `c3_label_sweep.py`; a sidecar only in the future D.3 runner (W1);
- (c) redefine `budget_frac_left` from worker runs now, with an equality test on execute-all tables (W2).

| Review finding | Change in this revision | Where |
|---|---|---|
| F1 wrong S0.6 sensitivity | Limits list now copies Track S §10: only P2+ concentrated calibrated | §3.7 item 6 |
| F2 π′ mis-described | π′ is a fork-fitted policy-improvement step nesting the static rule; the same-immediate-estimate contrasts are the budget DP and the fork-level hybrid estimate | §1, §2, §3.7 |
| F3 "no train/deploy mismatch" wrong | Claim withdrawn; feature and prompt line redefined from worker runs (W2) | §3.6, W2 |
| F4 conflict with R1-TRACKS-FRAMING | New amending row; outcome wording kept, RL-arm clauses replaced | §3.3, §9 |
| F5 vocabulary inconsistent | static / per-instance / **myopic** / **non-myopic**; "DAC" exempt; A1 per-instance; Track S m\* myopic | §3.2 |
| F6 ladder overstates the theorem | Reduction fails by construction in this harness; myopic control is a measured surrogate | §2.1, §2.3, §3.2 |
| F7 budget DP under-specified | Slot model, keep rule, freeze before S0.7, sweep replay dropped, n = 30 descriptive, conditional on binding W | W3 |
| F8 sidecar redundant, on the critical path | Archive + offline exporter; sidecar only in the D.3 runner; O1/O2 dropped | W1 |
| F9 W5 cannot discriminate | Full x_{1:n} encoding; incumbent-dependent features removed; A3 only; (NF-c) as quantification | W5 |
| F10 W4 repeats S0.6 | W4 = S0.6 extended with exact DP oracles; frozen with rev 8 before S0.7 | W4 |
| F11 AWR-MLP unclassified | AWR-MLP = single-step offline policy learning (not called RL); FQE/Longstaff–Schwartz secondary → Paper C | §2.2, §3.4 |
| F12 no Bayes-myopic reference in C3 | A2-U as a B.3 reference row (W6) | W6 |
| m1–m21 | DP cut in rev 5; collector inventory; critical path incl. R1-BX-D8-CONFIRM; seed-block exception deleted; C4 A/B left open; random matched-budget arm kept offline; T4 pointer moved out of T4; env docstring after the ack; full A7 reference list; setup/introduction listed; cost reporting specified; σ unit named; GPU extension left open; effort re-totalled; routing row requested; hybrid restored; leakage, seeds, per-tier reporting; one secondary table; W4 not loop evidence | throughout |

---

## 0. Summary

1. **The comment is right on the concepts and wrong on the scale for Paper B.** Its four-level claim ladder (dynamic control, future value, RL, decision model) and its demand to separate the C3 gate from Track S should be adopted now. Its Sequential Policy Track — behaviour-policy mixtures, repeated fork trees, offline and online multi-step RL — is a paper of its own and does not fit before 10 Jan 2027 next to the current critical path (B1 → B2 → X.7 → HK4–HK7 → R1-BX-D8-CONFIRM → B.7, with HoreKa 2 down 23 Nov – 4 Dec).
2. **Paper B keeps its shape:** C1 errors, C2 theory (one-step index theorem, reduction under (NF)+(NI), failure examples), C3 learned single-step belief under the rule, Track S as the campaign-level screen. What changes is **what Paper B claims** (§2), **how the documents describe RL, "dynamic" and the reduction** (§3), **one dependency** (Track S no longer sits behind B.7, and its outcomes no longer govern the RL arms), and **six cheap additions** (§4).
3. **The additions** cost about 12–17 desktop days including review rounds, at most about 1.5 % more Track S LLM calls (only if W3 runs), and no new GPU budget. None touches a Track S pin before S3e or the sweep runner:
   - W1 — a transition-logging contract met by archiving existing records and an offline exporter; a sidecar only in the not-yet-written D.3 runner;
   - W2 — `budget_frac_left` and the serialized budget line redefined from worker runs, identical on execute-all tables;
   - W3 — a budget dynamic-programming (stochastic-knapsack) rule, frozen before S0.7, run as a descriptive Track S secondary only if W binds;
   - W4 — S0.6's synthetic study extended with exact DP oracles, frozen before S0.7;
   - W5 — the (NI) masking test on A3 and a quantification of the (NF-c) failure;
   - W6 — A2-U (the history-updating Bayes-myopic rule) as a reference row in B.3.
4. **Paper B makes no claim about multi-step RL (L3).** A7 (online RL) leaves Paper B. R-B is described as single-step, offline policy-gradient training with a verifiable reward.

---

## 1. Assessment of the comment, item by item

Disposition: **Adopt** (now, in Paper B) · **Adopt, scaled** (a smaller version in Paper B) · **Paper C** (moved) · **Already in plan** (state it more clearly).

| Comment § | Point | Disposition | Where in this proposal |
|---|---|---|---|
| intro, §1 | Split into L1 dynamic control, L2 future value, L3 RL, L4 decision model; partial results are publishable | **Adopt** | §2 |
| §2.1 | Track S answers only a restricted L1 (four pre-specified members, A2-U, verify off, two CPU nodes, binding W by design, one-way; in the FIXTURE S0.6 study only P2+ concentrated calibrated) | **Already in plan** (Track S rev 7.4 §0 and §10 say all of this); state it in the manuscript's limits | §2.3, §3.7 |
| §2.2 | Track P targets are single-step; `env.py` terminates after one step | **Adopt** (wording) | §3.4, §3.5 |
| §2.3 | C3 gate failure must not veto Track S, and a Track S null must not stop C3 | **Adopt** | §3.3 |
| §3.1 | Episode = whole campaign; Y = final incumbent's audited value; don't mix raw and normalised units | **Already in plan** for Track S (raw Y, PLAN:118 departure declared); state the cross-node rule | §3.7 |
| §3.2 | State contents; the trial-indexed `budget_frac_left` is not remaining budget; equal information across arms | **Adopt** | W2 (§4.2), §3.6 |
| §3.3 | First round E1 execute/skip with a frozen acceptance rule; E2 keep/verify later | **Paper C** (Paper B's Track S already varies both thresholds; the staged action space is a Paper C design) | Paper C §3 |
| §3.4 | Terminal reward Y_T − Y_0; shaping only as a training tool; don't add g in the main objective under a fixed budget | **Paper C**; for Paper B, Track S already uses terminal audited Y | — |
| §4.1 | Keep Track S's primary comparison, rules and pre-declaration | **Adopt** | §3.7 |
| §4.2 B1 | Budget DP / stochastic knapsack as a strong non-RL sequential baseline | **Adopt, scaled**: a conditional, descriptive Track S secondary (the DP candidate was cut in Track S **rev 5**: "the budget member replaces it"), plus a synthetic-world oracle | W3, W4 |
| §4.2 B2 | Finite-horizon model-based rollout | **Paper C** | Paper C §7 (N5) and §5 (E-SIM) |
| §4.3 | Myopic vs continuation-aware with the **same** immediate estimate | **Partly in plan.** Track S π′ is *not* this contrast: it is a ridge score fitted on total fork Q differences, so it re-learns the immediate part too. In Track S the comment's form exists only as the fork-level hybrid estimate (index + Ĉ, descriptive) and, if run, the budget DP against m\* at m\*'s keep margin | §2.2, §3.7, W3 |
| §4.4 | Positive controls for budget, information, incumbent interaction, proposer feedback, strict null | **Adopt, scaled**: S0.6 extended with DP oracles, as sensitivity (not as a Track S gate) | W4 |
| §5 | Sequential Policy Track: transitions, behaviour mixtures, fork data, offline RL, online RL | **Paper C**, except the logging contract, which Paper B meets now from existing records | W1; Paper C §§4–7 |
| §6.1 | Control-policy baselines (default, execute-all, random, tuned static, myopic noise-aware, A2-U, dynamic budget threshold, DP, MPC, racing, LLM self-control) | **Mostly in plan** (A0, prac-1/2, A1–A4, Track S static/dynamic, A2-U in Track S). A2-U added to B.3 (W6). DP added (W3). Random at matched realised budget is already a required PLAN §5 baseline: kept offline in B.3; D.3 open (O3). MPC → Paper C | §4, §11 |
| §6.2 | Learning baselines: single-step SFT + rule, single-step action head, multi-step supervision, BC, DAgger, offline RL, online RL | Single-step ones **in plan** (R-A0, R-A1/2, Stage D, AWR-MLP as single-step offline policy learning). Multi-step supervision: π′ is a one-iteration fork-fitted improvement step (descriptive). BC, multi-step offline RL, online RL → **Paper C** | §2.2 |
| §6.3 | Architecture baselines (logistic/linear, LightGBM, MLP, no-text, plain LM, belief-only/action-only) | **In plan** (A3 LightGBM, TabPFN incl. information-matched, Qwen base control, context-only rung, R-A0 vs R-A1). MLP rung: open item O4 | §11 |
| §6.4 | Hindsight oracle and small-world DP oracle as diagnostics only | **In plan** (Track P §7.1 noisy-oracle ceiling; PLAN §5 hindsight oracle); DP oracle added with W4 | W4 |
| §7 | Mechanism attribution (budget, information, feedback, interaction) | **In plan** as Track S S2, S3a channel contrasts (Δ_B, Δ_I, Δ_F), S4a, S1.1. Powered versions → **Paper C** | §3.7 |
| §7.4 | Report low- and high-interaction environments separately | **Adopt** as descriptive per-tier reporting next to the pooled R1-BX-D8 gate (gate unchanged) | §5 |
| §8 | Layered matrix: synthetic → Track S CPU → harder tasks | Layers 1–2 **adopt**; layer 3 (powered multi-step on GPU tasks) → **Paper C** | §2.3 |
| §9 | Campaign as the unit; train/dev/test isolation incl. leakage beyond seeds; primary comparisons and multiplicity; no copying n = 300; training seeds | **Adopt** for every addition | §5 |
| §10 | Cost reporting incl. development cost | **Adopt, scaled**: Paper B reports GPU-h per arm including training, tokens and latency; amortisation of development cost over deployments → Paper C | §6 |
| §11 | Risk table | Paper-B-relevant rows folded into §7 | §7 |
| §12 | Order: concepts → state/action/data contract → Track S as approved → strong non-RL baselines → small-model RL → LLM multi-step RL | Steps 1–4 **adopt** (Paper B); steps 5–6 → **Paper C**. Step 2's bin-action vs execute/skip interface mismatch: the bin-action env is marked superseded for Track P in the documents (§3.4) | §4, Paper C |

**One thing the comment does not say, and Paper B should.** The manuscript draft (`papers/r1/sections/problem.tex`, `setup.tex`) calls per-proposal, forecast-driven configuration "dynamic". Under the reduction theorem that is a myopic (contextual-bandit) rule, not sequential control. The word has to be split (§3.2), or every reviewer who reads the comment's L1 will find the paper using "dynamic" for two different things.

---

## 2. What Paper B claims after the revision

### 2.1 The claim ladder

| Level | Question | What Paper B provides | What it does **not** claim |
|---|---|---|---|
| **L0 (new name for C1–C2)** | Does noise make the default loop err; what is the optimal one-step rule; when is one-step control globally optimal? | C1 measured errors; C2 one-step index theorem (Prop 8′ in the revision draft), the winner's-curse result, the reduction theorem under (NF)+(NI), and the two unbounded-loss failure examples. **In the governed loop the reduction's conditions fail by construction** (hard budget; filtered duplicates consume a trial and a call, so (NF-c) fails; possibly a shared incumbent error, T4 revision R1). Myopic control is therefore a surrogate whose campaign value is measured (D.3) and whose non-myopic headroom is screened (Track S) | Global optimality of myopic control in this loop; that failure of a condition implies a non-myopic gain (failure is necessary, not sufficient) |
| **L1 non-myopic (sequential) control** | Does a state-dependent threshold beat a tuned static one on whole campaigns? | Track S, one-way screen, on the declared nodes; the matched-static guard; S0.6 sensitivity (only P2+ concentrated calibrated) and its extension (W4) | Absence of sequential value from a Track S null; anything about the four-member family beyond π\*; sensitivity in the budget, information or negative-feedback channels |
| **L2 future value** | With the same immediate estimate, does adding a continuation term help? | Descriptive only: the fork-level hybrid estimate and the S3a channel contrasts; the budget DP vs m\* at m\*'s keep margin (W3, if run); π′ as a fork-fitted policy-improvement step (not a same-immediate contrast); W4 oracle gaps in synthetic worlds | A powered L2 result (Paper C) |
| **L3 RL** | Does multi-step RL beat strong non-RL sequential methods? | Nothing | Any L3 statement. R-B is single-step policy-gradient training |
| **L4 decision model (single-step)** | Does a model that reads the proposal beat structured forecasters, at equal information? | C3 ladder (A3, TabPFN incl. information-matched, Qwen control, Kev, A4 self-control, A2-U reference), aggregate gate, leave-one-suite-out, D.3 closed loop | Multi-step decision-model value (Paper C) |

### 2.2 Which method sits at which level

| Method in the plan | Level | Correct description |
|---|---|---|
| A1 | per-instance prior under the one-step rule | Constant prior fitted on the node's campaigns |
| A2–A3, A5 + rule (R-A0) | L4 (myopic) | Learned prior under the one-step rule |
| A2-U (W6, reference) | L4 (myopic, Bayes) | History-updating Bayes-myopic rule; the theorem's one-step policy under its model |
| R-A1/R-A2 action head | L4 (myopic) | Decision-focused fine-tuning (cost-sensitive classification) |
| R-B (optional) | L4 (myopic) | Single-step, offline policy-gradient training (GRPO-style) with a verifiable per-proposal reward; a contextual-bandit RL arm. The only arm the paper calls RL (R1-BX-D9). Not multi-step RL |
| AWR-MLP (PLAN §5 required baseline) | L4 (myopic) | Advantage-weighted regression on the per-proposal reward: single-step offline policy learning (offline contextual-bandit learning), described that way and not called RL, consistent with R1-BX-D9's naming rule |
| Stage D (one DAgger round, 1–2 T1 nodes) | L4 | On-policy state aggregation; evidence of state-distribution shift, not of a policy-value gap (R1-WORDING-30OCT) |
| Track S `static` (m\*) | myopic, tuned constant threshold | Tuned (g, h) on A2-U's per-proposal, history-updated V̂\* |
| Track S `dynamic` (π\*) | L1 (non-myopic, single channel) | Tuned state-dependent thresholds |
| Track S π′ | L2 (descriptive) | Ridge score fitted on total fork Q differences (features incl. V̂\*, m̂, budget terms), acting iff f̂(s) > 0: one fork-fitted policy-improvement step that nests the static rule; **not** a same-immediate-estimate contrast |
| Track S fork-level hybrid (index + Ĉ) | L2 (descriptive fork quantity) | The comment's "same immediate estimate plus continuation" form, at fork level only |
| Budget DP (W3, new) | L1/L2 (descriptive) | Execute iff V̂\* exceeds the continuation value of a run; same immediate estimate as m\*, keep at m\*'s margin |
| Two-step continuation-value rule (Longstaff–Schwartz / FQE, PLAN §5 secondary) | multi-step | **Moves to Paper C** (it is a multi-step continuation-value method) |
| A7 online RL | — | **Leaves Paper B** (Paper C) |

### 2.3 Revised contributions (PLAN §3 box, proposed wording)

> **C1** — measured control errors and wasted runs (unchanged).
> **C2** — theory: the one-step index theorem; the reduction of the loop to independent one-step (contextual-bandit) decisions under no feedback and no information at a fixed run price; unbounded-loss examples when either condition fails; the hard-budget case as a declared non-theorem. In the governed loop the conditions fail by construction, so the theory says where non-myopic control *can* help, not that it does. One offline implication is checked on A3 (W5).
> **C3** — a learned single-step belief under the C2 rule: does it close the gap to the noisy oracle beyond the index policy, the Bayes-myopic reference, structured forecasters, LLM self-control and the hybrid, at equal information (L4)?
> **Sequentiality screen (Track S)** — does a tuned state-dependent policy beat the tuned static rule on whole campaigns (L1, one-way)? Descriptive L2 evidence from the fork contrasts and, if run, the budget DP. The screen's measured sensitivity is one calibrated control (P2+ concentrated); other channels are unmeasured.
> **C4 (secondary, appendix)** — the decision-independence diagnostic on forced keep/discard pairs, descriptive. Online RL moves to Paper C; where the debiased-memory A/B goes is open (O6).
> **Not claimed:** the value of multi-step RL, or of multi-step training of the decision model. No secondary quantity enters the abstract or the contribution list.

This keeps the novelty position the author set on 23 Oct (the self-control vs trained vs hybrid comparison) and answers the worry that "DAC + RL-trained configurator" alone is thin: the DAC contribution is the **reduction result plus a measured screen**, not an RL claim.

---

## 3. Revisions, document by document — what and how

Each item names the file, the problem, and the replacement. "Row" means a PLAN §10 draft row in §9. The editor follows the routing the author records (row R1-SEQ-ROUTING, §11 O8).

### 3.1 PLAN §2–§3 (the question and the contributions)

- **Problem.** §2 still lists "How much does learning add?" with RL implicit; the §3 box says "C4 also decides whether online RL (A7) is warranted".
- **How.** Insert the §2.1 ladder after §2's question as "Claim levels (Nov revision)". Replace the §3 box by the §2.3 wording. Delete the A7 sentence from C4. Row **R1-SEQ-CLAIMS**.

### 3.2 Vocabulary: "myopic" vs "non-myopic" configuration

- **Problem.** `problem.tex` and `setup.tex` name three levels — static, per-instance, dynamic — and define "dynamic" as per-proposal, forecast-driven (A2–A6 under "Dynamic"). Track S's "dynamic" means state-dependent (budget, uncertainty). The comment's L1 uses the Track S meaning. "Contextual" is not a usable replacement: it collides with contextual DAC (context = instance features), which `problem.tex` cites, and with the context-only rung A1-ctx. "History" does not separate the levels either, because A3, A5 and A2-U already use the history.
- **How.** Four levels everywhere (manuscript, PLAN, TECH_ROUTE, C3_DESIGN, Track S design §0):

  | Level | Definition | Where |
  |---|---|---|
  | static | one configuration for every instance and trial | A0, prac-1 |
  | per-instance | set once per instance (fitted, or predicted from descriptors) | A1, A1-ctx |
  | **myopic** | per proposal, through a one-step rule on a per-proposal forecast (which may use the history); optimal under (NF)+(NI) at a fixed price | A2–A6, A2-U, R-A/R-B, AWR-MLP, Track S m\* (myopic with a tuned constant threshold) |
  | **non-myopic** | thresholds that depend on future-value state (remaining budget, uncertainty, feedback state) | Track S π\* (single channel), π′, budget DP |

  The term **"dynamic algorithm configuration" (DAC)** is kept for the problem class — the configuration changes during the run — and is exempt from the rule; "dynamic" as a *level* is not used. The manuscript sentence becomes: *"In DAC terms, myopic configuration is optimal when the DAC problem reduces to a contextual bandit (Theorem 1). Non-myopic control can help only where the reduction fails. In the governed loop it fails by construction (a hard budget, duplicate filtering, possibly a shared incumbent error), so myopic control is a surrogate whose campaign value we measure (D.3) and whose non-myopic headroom we screen (Track S)."* Row **R1-SEQ-VOCAB**.

### 3.3 The C3 gate and Track S become parallel branches; R1-TRACKS-FRAMING amended

- **Problem.** In the 18 Oct design the only sequential measurement (the online pilot and A7) sat behind the one-step gate (Track S design §0), and TECH_ROUTE's dependency graph still has no Track S chain at all. T4 revision R4 already says the gate's scaled one-step gain has no guaranteed sign relation to the campaign gain outside (NF)+(NI). Separately, the adopted row **R1-TRACKS-FRAMING (30 Oct)** ties Track S outcomes to "the RL arms" (keep them on an information/keep-channel A; optional on a budget A; not needed on no gain). Since R1-BX-D9 the only arm called RL is R-B, a single-step optional ablation; a Track S outcome measures non-myopic value, which a single-step method cannot use. The link is therefore not meaningful, and it contradicts R1-SEQ-GATES-PARALLEL.
- **How.**
  - State in RUNBOOK (Phase B, Track S, §6) and TECH_ROUTE: B.7 failing does not stop or reweight Track S; Track S's outcome does not change B.7, Phase C or R-B. Phase C still requires B.7 (unchanged). Track S keeps its own STOPs, host priorities (Track X on TASL-2, Track P on TASL-7) and its ≈ 15 Dec fallback. In TECH_ROUTE's mermaid graph, Track S is a separate chain from host preparation to "manuscript claims", with no edge from the gate. Row **R1-SEQ-GATES-PARALLEL**.
  - **Amend R1-TRACKS-FRAMING** (row **R1-SEQ-TRACKS-FRAMING-AMEND**). Keep the four outcome → headline-wording mappings unchanged ("noise-aware DAC" headline; "budget-coupled index control"; "no dynamic claim" for a threshold-level shift; "noise-aware DAC and when it reduces to one-step decisions", never claiming the loop is one-step). Replace every "RL arms" clause by: (i) R-B's place is decided only by B.7 and time (R1-BX-D9), whatever Track S finds; (ii) a route-A outcome on any channel is recorded as motivation for non-myopic learned control in the follow-up paper, and a no-gain outcome as "not motivated on these nodes at this sensitivity"; (iii) no Track S outcome motivates multi-step RL in Paper B.
  - **Timing.** Track S is at the S0.1 re-run; no screen outcome exists. The amendment is valid only if committed before any S3e outcome is read, as R1-TRACKS-FRAMING itself requires ("declared before any outcome"). Preferably before S0.4.
- This changes no execution today: Track S has never waited for B.7 in the current runbooks.

### 3.4 RL wording in Track P, C3_DESIGN, RUNBOOK and TECH_ROUTE

| File and place | Current text (gist) | Replacement |
|---|---|---|
| `TRACK_P_POST_TRAINING.md` §1, positioning note | "Stage D (DAgger) is the empirical evidence for (b)" | "Stage D measures state-distribution shift under the deployed configurator; it is not evidence of a policy-value gap or of sequential value (R1-WORDING-30OCT). Whether the full loop needs non-myopic control is Track S's question (L1)." |
| same, §1 table, "Action" row | "skip / execute; after execution keep / reject" | add: "Track P trains single-step targets only; the offline environment terminates after one step. The 12-bin action env is superseded for Track P (R1-C3-POST)." |
| same, §6.4 heading text | "reasoning arm (GRPO)" | add: "R-B is single-step, offline policy-gradient training against a verifiable per-proposal reward; it is the only arm the paper calls RL (R1-BX-D9), and it makes no multi-step claim." |
| `C3_DESIGN.md` §2 point 5 | per-proposal reward is "valid under DI, T4 Proposition 10" | "The per-proposal reward is the one-step objective of the index theorem (revision Prop 8′) and needs no independence condition. Its sum equals the campaign objective only under (NF) and (NI) (reduction theorem), which fail by construction in this harness; it is a declared one-step quantity (T4 revision R3, R4)." |
| `C3_DESIGN.md` §5, row (A7); §7 ("decides whether A7 is needed"); §8 risk row | A7 as stage 3 online RL, gated by the DI test | "(A7) moved to Paper C (R1-SEQ-A7-MOVE). A DI violation is necessary, not sufficient, for any non-myopic gain (reduction theorem, contrapositive)." |
| `C3_DESIGN.md` §5, ref row | "AWR-MLP acting on actions directly" | add: "single-step offline policy learning on the per-proposal reward; not called RL." |
| `C3_DESIGN.md` §5 "Stage 2, precisely" | still describes the old 12-bin action and greedy-bin deployment | mark as superseded history (R1-C3-POST), with a pointer |
| `RUNBOOK.md` §6 row "DI strongly violated (C4)" | "One-step offline values are biased; A7 (online RL) becomes justified, with T4 Proposition 10(b)" | "Report it with the reduction theorem's contrapositive: a violation is necessary, not sufficient, for a non-myopic gain. Offline one-step values are declared quantities, not campaign estimates. Online RL is Paper C." |
| `RUNBOOK.md` H.7 (AWR-MLP row), H.8, Track H open items | AWR-MLP as a direct-action arm; H.8 amendment conditional on A7/C4 | AWR-MLP described as above; H.8: "deferred; needed only by Paper C" (R1-H8-DEFERRED's trigger changes from "A7/C4" to "Paper C") |
| `TECH_ROUTE.md` Track H row | online env for A7 | "Paper C" |
| PLAN §5 secondary list | "two-step continuation-value rule (Longstaff–Schwartz / FQE) for budgeted verify" | moved to Paper C (verify is off in Paper B) |
| `r1/c3/env.py` docstring (lines 1–27, incl. `OnlineCampaignEnv` "only if C4 finds a material DI violation") | "Offline contextual-bandit environment" | no code change; one docstring line "one-step by design; not a model of the campaign", and `OnlineCampaignEnv` → "Paper C". **Deferred until R1-B2-REPAIR-SCOPE-ACK** is resolved, because `env.py` is a shared file with a pending out-of-scope change (`9bab3d6f`); STOP-and-ask applies |

Rows **R1-SEQ-RL-WORDING** and **R1-SEQ-A7-MOVE**.

### 3.5 Theory documents

- **Problem.** `theory/T4_FEEDBACK_PROPOSER.md` still carries the old Prop 10(a) and its §6 "Reading" (RL-necessity claims). The manuscript already uses the revised statements.
- **How.** No change to T4 before the author's proof check: R1-T4-DI-FIX keeps it "unchanged". Put the pointer in PLAN (next to R1-T4-DI-FIX) and in TECH_ROUTE instead: "T4 §6 'Reading' is superseded in the manuscript by `proposals/T4_PROP10_REVISION_20261028.md` §3 contrapositive and R5." The open items of R1-T4-DI-FIX stay with the author: R1 (incumbent-error model), R4 (does the gate's "20" count proposals or executed runs), and which §6 tests enter the plan — this proposal recommends one (W5).

### 3.6 Budget fields in features, prompts and logs

- **Problem.** The C3 feature `budget_frac_left` (`r1/c3/features.py`:98, 257, 385) is `1 − (b − 1)/runs_total`, indexed by trial. In execute-all sweeps the trial index ≈ runs used + 1, so it equals the remaining-run fraction. Under a skipping arm with W binding and a trial budget equal to the LLM cap (≥ W, `r1/c3/control.py`:351–363), it is not: it goes negative once b > W + 1, outside the training support (Track S H7 found exactly this). Worse, the decision-model prompt (`r1/c3/train/serialize.py`:97–98, 186) tells the model "trial b of W (max(W − (b − 1), 0) worker runs left)", which is false for every skipping arm, so A5/A6 would be shown wrong information in D.3. Revision 1's claim of "no train/deploy mismatch" was wrong.
- **How.** W2 (§4.2): redefine the feature and the serialized budget line from worker runs used/remaining. On execute-all tables the values are identical, so labels, sweep 1 and B.3 are unaffected. Every campaign record keeps worker runs used and left, LLM calls used and left, and proposal slots left (derivable for existing runners, W1). Row **R1-SEQ-BUDGET-FIELDS**.

### 3.7 Track S design (rev 7.4 → a short rev 8, documents first)

Track S's primary comparison, families, n = 300, Holm rule, placebos, decision routes, π′'s definition and refit rule, and the S0.1 pins (paper `d10b05b7`, harness `a3fedbb`, operator runbook rev 3.3 @ `13badb0`) stay **unchanged**. Rev 8 is committed **before S0.7 starts** (so that nothing in it can be shaped by dev outcomes), preferably before S0.4:

1. **§0 framing.** One paragraph mapping Track S to the ladder: primary = L1 screen; fork-level hybrid, S3a contrasts, π′ and (if run) the budget DP = descriptive L2; nothing about L3. π′ is described accurately: "a fork-fitted policy-improvement step that nests the static rule; not a same-immediate-estimate contrast".
2. **Budget-DP secondary (W3).** The algorithm (slot model, discretisation, keep rule, value distribution source) is specified and frozen in rev 8; only its empirical V̂\* input is filled in after S0.7. It runs on the existing 30-instance secondary subset of S3e **only if W binds** (S0.5b) and its collector code passes review before S3e. It cannot move the route.
3. **Records for Paper C (W1).** No collector change. `$WORK/roots/*/root_trials.jsonl`, `root_events.jsonl` and the leaves' `branch_*` files are archived with sha256 before Track S closes; an offline exporter maps them to the W1 schema with a gap list.
4. **Synthetic sensitivity (W4).** S0.6 extended with exact DP oracles; worlds and target gains frozen in rev 8; reported as "additional sensitivity, not a Track S gate". S0.6's STOP rule and its calibrated controls are unchanged.
5. **Cross-node unit rule.** Per-node primary in raw audited Y (as now). Any cross-node summary uses Y/σ_cmp,vary from S0.5b, declared before S3e; raw units are never averaged.
6. **Manuscript limits list**, copied from design §0 and §10: four pre-specified members; A2-U is a model-based Bayes-myopic controller and not the deployed C3 rule; verify off; two CPU nodes (whether GPU nodes enter the decision is open under R1-BX-D10 and M6's design revision); W chosen to bind; one-way; **only the concentrated positive keep-feedback control (P2+ concentrated) calibrated in the FIXTURE study at n = 300 (1.04 δ_Y, power 0.86 [0.80, 0.90]); P2+ diffuse and P1-diffuse did not calibrate, and the budget, information and negative-feedback channels are unmeasured; the per-node values are the final S0.6 values.**

**Pins.** Items 1 and 3–6 are documents and analysis only and need no new pin. Item 2 is the only Track S code: if adopted, it lands at a new pin that applies from S3e on, with a row amending R1-TRACKS-S01-RERUN, an operator-runbook revision and the S0.9 note; S0.1–S3a stay on `d10b05b7`. If the author prefers no Track S pin change, W3 runs in the synthetic worlds only. Row **R1-SEQ-TRACKS-REV8**.

### 3.8 Manuscript (`papers/r1/`)

| Section | Change |
|---|---|
| `introduction.tex` | four-level vocabulary where "dynamic" is used as a level (§3.2) |
| `problem.tex`, DAC paragraph | four levels; the "myopic configuration is the reduced case; the reduction fails by construction here" sentence |
| `setup.tex`, "Configuration policies" | A1 per-instance; A2–A6 "myopic"; A2-U reference row (W6); AWR-MLP described as single-step offline policy learning |
| `setup.tex`, offline gate | replace the "≥ 2 nodes" criterion by R1-BX-D8 (aggregate) once R1-BX-D8-CONFIRM exists (already pending, M11/M8) |
| `theory.tex`, "Scope" | add: "Under a hard budget the problem contains a stochastic-knapsack component; Track S's budget member (and, if run, a budget-DP secondary) probe it empirically." |
| `theory.tex`, "Consequences" | the ladder in two sentences: the theorem says where non-myopic control can help; in this harness its conditions fail by construction; Track S screens for headroom; nothing here concerns which learning method would exploit it |
| new results structure | results ordered by level: L0 (errors, theory check W5), L4 (C3 ladder, gate, transfer, D.3), L1/L2 (Track S, synthetic sensitivity) |
| `limitations.tex` | Track S limits (§3.7 item 6); single-step training only; no multi-step RL; offline evaluation of skipping is optimistic for Bayes-myopic controllers under (NF) (already in `setup.tex`, T4 revision R6) |
| future work (one paragraph) | "multi-step policies and their learning are studied separately", with no promised results |

---

## 4. New work items for Paper B

### 4.1 W1 — transition-logging contract, archive and offline exporter (desktop; 1.5–2 days)

- **Spec.** `docs/r1/TRANSITIONS_SPEC.md` (proposed name): one record per decision point, so that every campaign Paper B runs is reusable as multi-step data later. Fields (full schema in Paper C plan §4.1): identity (node, instance, campaign, root/fork ids, step, epoch, policy string and version, action, action probability, eligible vs rule-forced, seed key and repetition); state (proposal hash and edit, incumbent hash, duplicate/no-op flags, the controller's forecast, worker runs used/left, LLM calls used/left, proposal slots left, keeps/skips so far); outcome; episode end (`terminated` vs `truncated`, with reason; divergence as an outcome); terminal Y and its audit seeds; environment constants (W, LLM cap, memory mode, edit schema, proposer).
- **Inventory of what exists** (revision 1 understated it). The Track S collector already writes per decision `r` (the worker-run budget gap), `tau_pred`, `margin`, `skip_reason` and `eligible` beyond the schema comment (`collect.py`:768–803); the full forecast (π, μ, τ, σ, V\*, m̂, key, candidate projection sha) is in `root_events.jsonl` (`control_decision` details); the harness ledger is `root_trials.jsonl`. Sweeps are execute-all; their transitions are derivable from `root_trials.jsonl` and `root_events.jsonl`, which `e1b_collect` already writes. Track S leaves (`LeafRecord`) store the fork state, arm, `y_terminal`, runs used and the first next proposals, not post-fork decisions; the leaf ledgers must be archived for bootstrapped use later.
- **How the contract is met.**
  1. **Archive** (sha256 manifest) of `$WORK/roots/*/root_trials.jsonl`, `root_events.jsonl` and the leaves' `branch_*` files before Track S closes, and of each sweep's run directories after the sweep (sweep 2 T0, HoreKa T1).
  2. **Offline exporter** to the W1 schema, with a per-field gap list. Acceptance: on a sample of campaigns per runner, every exported budget and incumbent field agrees with the ledger (wall-clock fields excluded).
  3. **Sidecar only in the D.3 runner**, which does not exist yet: logging only, a normalised-ledger equality test (wall-clock fields excluded), and a fail-safe rule (a sidecar exception never truncates or alters a campaign).
- **What is not touched.** No Track S collector change and no new Track S pin for logging; no change to `r1/scripts/c3_label_sweep.py` (already edited by M3, M4 and HoreKa §3 items 3 and 5 on the O6/HK6 path); no runner change between the HK5 pilot and HK6.
- **Owner.** Spec and exporter: per R1-SEQ-ROUTING (proposed: chat session, with a fresh-agent review). D.3 sidecar: M15/O11 when the runner is written.

### 4.2 W2 — budget fields from worker runs (desktop; 0.5–1 day + review)

- **What.** In the replay and the deployed view, define `budget_frac_left` from worker runs used/remaining, and change the serialized budget line in `r1/c3/train/serialize.py` to the true worker runs left (and, where shown, LLM calls left).
- **Test.** On every execute-all table (sweep 1; sweep 2 when it exists), the new feature is identical to the current one, and the serialized prompts are byte-identical. Any difference is a STOP.
- **Deadline.** Before sweep 2's features are frozen and before any Track P template freeze (M13 owns `r1/c3/train/`); in any case before A5/A6 are trained on the feature.
- **D.3.** The D.3 LLM-call cap must be declared in D.3's pre-declaration, so that "proposal slots left" is defined.
- **Owner.** Per R1-SEQ-ROUTING (proposed: Mac-local, within M13's scope for `serialize.py`; `features.py` STOP-and-ask if another thread holds it).

### 4.3 W3 — budget-DP rule (desktop; ½ day spec in rev 8, 1.5–2 days code and tests if run)

- **Rule.** Execute iff the current proposal's one-step value V̂\*_n exceeds the continuation value of one run, given runs left and proposal slots left; the continuation value is computed by backward induction over (runs left, slots left).
- **Specified in rev 8, before S0.7:**
  - (a) **Slot model.** Slots left = min(trials left, calls left + 1), as `a2u.budget_gap`. Rule-skipped duplicates and no-ops consume a slot (and a call) with V̂\* = 0; their per-slot rate is a parameter estimated with the V̂\* distribution.
  - (b) **Value distribution.** V̂\* i.i.d. from its empirical distribution over m\*'s S0.7 dev decisions per node (no new dev campaigns); discretisation fixed in rev 8.
  - (c) **Keep rule.** The DP keeps at **m\*'s keep margin h**, so the DP-vs-m\* contrast differs only in the execute decision (the comment's same-immediate-estimate form).
  - (d) **Interpretation limit.** The i.i.d. future-value model ignores dependence on the incumbent and the history; it is a model-based heuristic, not an optimal policy, and is described that way.
- **Uses.** (i) A descriptive Track S secondary on the existing 30-instance subset of S3e, **only if W binds** (if no W binds, the budget member is dropped, the DP reduces to g = 0, and W3 is not run in Track S); (ii) in the synthetic worlds (W4), where the exact DP optimum is also computable. Revision 1's offline replay on sweep ledgers is dropped: sweeps are execute-all with one proposal per run, so runs left ≥ slots left always holds and the DP trivially executes everything, and freed runs cannot be re-spent on logged proposals (22 Oct run-accounting row).
- **Precision, stated in advance.** At n = 30 the interval is about √(300/30) ≈ 3.2 times wider than the primary's; the expected half-width is pre-stated from S0.5's σ_D. The result is expected to be uninformative and is reported as descriptive.
- **Cost.** About +30 campaigns per Track S node, ≈ 1.2k LLM calls (≈ 1.5 % of the ≤ 79k planned), only if run. It is new collector code (`collect.py`:475: "budget_dp / probe_first are not implemented"); see §3.7 on the pin.

### 4.4 W4 — S0.6 extended with exact DP oracles (desktop CPU; 2–3 days)

- **What.** The existing S0.6 worlds — N0 (strict null), P0 (budget), P1 (information), P2± (keep feedback) — plus an incumbent-interaction world (B valuable only after A is kept, or A blocks B), each with the **exact DP-optimal value** where the state space allows, and with π′ and the budget DP reported in every world next to the best static rule and each Track S member.
- **Calibration.** As S0.6: target gains stated in advance, calibrated by large replication (10⁴ per world, ±5 %). Worlds are not fitted to members (rev 7.1 q4: circular).
- **Freeze.** Worlds and target gains are frozen with rev 8, **before S0.7 starts** (revision 1's "before S3e" was too late: S0.7 dev outcomes and S3a fork contrasts would be known).
- **Status.** Pipeline sensitivity only, never evidence about the real loop. S0.6 found no world variant giving the budget member a calibratable δ_Y gain; the budget channel stays **unmeasured** for the Track S family unless a non-circular world calibrates. W4 supplies the content of R1-BX-D10's fallback ("theorem plus synthetic controls") if Track S has no campaign-level result by ≈ 15 Dec, explicitly as pipeline sensitivity, not loop evidence.

### 4.5 W5 — one offline check of the reduction theorem (desktop CPU; 0.5–1 day after labels)

- **(NI) masking test, on A3 only.** Two A3 forecasters, both given a **sufficient encoding of the whole proposal history x_{1:n}** (all earlier edits, without outcomes) — not only the current summary features, since a forecaster given less than x_{1:n} can gain from results even under (NI) (T4 revision note on x_n). One also receives executed results. **Every incumbent-dependent feature** (`old_num`, `log_ratio`, `cfg_equals_incumbent`, `active_equals_incumbent`) is removed from both, or the incumbent is fixed to the start configuration, because the incumbent path leaks results under keep. Compared out of sample on RPS and decision utility (sweep 2 T0, and T1 where labelled), with 3 training seeds reported. An improvement beyond estimation error is evidence against (NI); its absence does not establish (NI).
- **A masked A5** would need a second SFT run on TASL-7 (no GPU training on the Mac, R1-COMPUTE); not included unless the author authorizes a TASL-7 job (O9).
- **(NF-c) quantification.** Report "the share of the horizon consumed by policy-dependent duplicates under A3's deployed rule", described as quantifying a failure that is known to be large (duplicates were 727 of 841 rule-detectable pilot proposals; Track S H3), not as a test.
- **Owner.** M14 (B.3 offline arms), after R1-BX-D8-CONFIRM. Row **R1-SEQ-THEOREM-CHECKS** (resolves R1-T4-DI-FIX's open item for this check only).

### 4.6 W6 — A2-U as a B.3 reference row (desktop CPU; ½ day)

- **Why.** The comment §6.1 warns that beating A2 but not the Bayes-myopic rule does not show value. A2 ignores the history and is not the Bayes-myopic rule (R1-WORDING-30OCT); the theorem's optimal one-step policy is Bayes given the history. A2-U exists only in Track S.
- **What.** A2-U with its prior fitted on the B.3 training partition, as an offline **reference row** in B.3 (and optionally in D.3). The R1-BX-D8 gate (vs A2) is unchanged. CPU-only; the code exists on `trackS-ops` (`r1/tracks/a2u.py`). Also kept offline in B.3: the PLAN §5 "random at matched realised budget" baseline (free offline). Row **R1-SEQ-A2U-REF**.

### 4.7 What Paper B does not add

- No exploratory (ε-random) campaigns, no repeated fork trees, no transition model, no MPC, no behaviour cloning, no offline or online multi-step RL, no multi-step training of any decision model, no continuation-value (Longstaff–Schwartz/FQE) rule. All are in the Paper C plan.
- No new arm in D.3 beyond the optional A2-U reference. The budget-DP rule stays in Track S and the synthetic worlds (O5).

---

## 5. Statistical rules for the additions

- **Unit.** The campaign instance; paired differences within an instance (comment §9.1). Trials inside a campaign are never independent units.
- **Primary comparisons are unchanged:** Track S's π\* vs m\* (Holm, one-way) and the C3 aggregate gate (R1-BX-D8). Every addition is a declared secondary or descriptive quantity; none uses Track S's Holm budget or can move a route.
- **One secondary table, fixed order.** All descriptive secondaries (matched static, the other members, π′, A2-U at g, budget DP, channel contrasts, W4 worlds × methods, W5) go into one pre-declared table in a fixed order. No secondary enters the abstract or the contributions. A secondary whose interval excludes 0 is reported with the number of secondaries examined.
- **Isolation.** The budget DP has no free coefficient once rev 8 freezes it: its value distribution and slot-skip rate come from m\*'s S0.7 dev decisions, and it is evaluated only on the S3e secondary subset. Synthetic worlds use their own RNG seeds. W5 uses the C3 train/validation/test partitions as declared for B.3. **Leakage beyond seeds** (comment §9.2): W5 and W6 report whether shared edit templates or start configurations cross the B.3 partitions; they use the existing grouping of recurring (candidate, incumbent) pairs.
- **Seed blocks.** Paper B reserves no new instance-seed blocks. The 7001–7005 / 7006–7010 audit rule keeps its present use. Paper C reserves its own blocks (Paper C plan §11).
- **Training seeds** (comment §9.5): W5's retrained A3 forecasters are run with 3 seeds, and the spread is reported.
- **Per-tier reporting** (comment §7.4): next to the pooled T0+T1 gate (R1-BX-D8, unchanged), B.3 reports T0 and T1 separately, descriptively.
- **Sample sizes.** No addition is powered. They are reported with intervals and as descriptive.

---

## 6. Cost and schedule

| Item | Owner (proposed; R1-SEQ-ROUTING) | Effort | Server cost | Must be done by |
|---|---|---|---|---|
| Document and wording revisions (§3.1–§3.6) | chat session | 1–1.5 days | none | before the next runbook revision |
| R1-TRACKS-FRAMING amendment row | author | — | none | before any S3e outcome; preferably before S0.4 |
| Track S rev 8 document (incl. W3 spec, W4 worlds) + review | chat session, M6 review | ½–1 day + review | none | before S0.7 |
| W1 spec, archive, exporter + review | chat session | 1.5–2 days + review | none | archive before Track S closes; exporter by end of Dec |
| W2 budget fields + tests + review | Mac-local (M13 scope) | 0.5–1 day + review | none | before sweep-2 feature freeze and Track P template freeze |
| W3 budget DP code + tests + review (only if adopted and W binds) | M6 | 1.5–2 days + review | ≈ 1.2k LLM calls per Track S node | before S3e |
| W4 synthetic worlds + review | chat session | 2–3 days CPU | none | frozen before S0.7; report by 8 Dec |
| W5 masking test, (NF-c) quantification | Mac-local M14 | 0.5–1 day | none | with B.3 (after labels and R1-BX-D8-CONFIRM) |
| W6 A2-U reference row | Mac-local M14 | ½ day | none | with B.3 |
| Manuscript changes (§3.8) | M8 / author | 1 day | none | Dec |

Total ≈ 9.5–13 desktop days of work, plus 2–3 review rounds on the four reviewed items (≈ 3–4 days), so **≈ 12–17 desktop days**, spread so that only W2 sits near the critical path. The Mac-local agent's critical-path items (M2, M3, M10, M11) keep priority. The dates of R1-BX-D14 are not changed. **Cost reporting in Paper B** (comment §10, scaled): per arm, GPU-h including training, tokens, and controller latency; amortisation of development cost over deployments is Paper C's.

---

## 7. Risks specific to this revision

| Risk | Consequence | Mitigation |
|---|---|---|
| The archive misses files before `$WORK` is cleaned | Track S forks lost as Paper C data | Archive with a sha256 manifest at the end of each Track S stage and before Track S closes; the exporter's gap list is checked against the manifest |
| W2 changes features on execute-all tables | Labels or B.3 comparability break | Equality test on every execute-all table; any difference is a STOP |
| Adding secondaries after seeing Track S data | Post-hoc analysis | Rev 8 committed before S0.7; otherwise the additions are labelled exploratory |
| The R1-TRACKS-FRAMING amendment lands after an outcome | Looks like re-framing after results | Commit before any S3e outcome is read (preferably before S0.4) |
| Synthetic worlds built to favour a method | Circular sensitivity claims | Worlds and target gains frozen before S0.7; strict null included; all methods in all worlds; not fitted to members |
| A W3 pin change disturbs Track S | Pairing or identity breaks | Pin change only from S3e, with the arm-invariance tests and a review; or W3 in synthetic worlds only |
| Desktop capacity | Critical-path Mac items slip | Chat session takes documents, W1, W4; Mac-local takes W2, W5, W6 inside existing M13/M14 scope; W3 only if adopted |
| Reviewers still read "DAC" as "needs RL" | Novelty attacked from the RL side | §3.2 vocabulary; claim ladder; explicit "not claimed" line |

---

## 8. Effects on the three threads

| Thread | Change |
|---|---|
| **Mac-local** | M13: W2 (`serialize.py`, `features.py` with STOP-and-ask) before the template freeze. M6: Track S rev 8 review; W3 code only if adopted. M8: manuscript changes §3.8. M14: W5 and W6 (A2-U and random-matched-budget rows). M15: D.3 runner sidecar. **No change to M2, M3, M4, M10, M11 or their order.** |
| **Operator** | O3: unchanged through the S0.1 re-run and S0.4–S3a on `d10b05b7`; archive step added at the end of each Track S stage; a new pin only from S3e and only if W3 is adopted. O6: unchanged runner; archive step after the sweep. O11: D.3 runner with the sidecar. No new runs except W3's ≈ 30 campaigns per node if adopted. |
| **HoreKa** | HK6/HK7: no runner change (none between HK5 and HK6); archive step after HK6. No new jobs and no budget change. |

---

## 9. Draft PLAN §10 rows (for the author)

```
| R1-SEQ-CLAIMS (date) | Paper B's claims follow the four-level ladder of `proposals/SEQUENTIAL_POLICY_REVISION_20261104.md` (rev 2) §2: L0 (errors; one-step and reduction theory, whose conditions fail by construction in the governed loop, so myopic control is a measured surrogate), L4 myopic (C3, with the A2-U reference), L1 non-myopic control (Track S, one-way screen; one calibrated control), L2 descriptive only (fork-level hybrid and channel contrasts, budget DP if run, π′ as a fork-fitted improvement step, synthetic oracle gaps). No claim about multi-step RL (L3) or multi-step training of the decision model. No secondary quantity enters the abstract or the contributions. PLAN §3's box is replaced by §2.3 of that proposal. |
| R1-SEQ-VOCAB (date) | Configuration levels are static, per-instance, myopic (per proposal through a one-step rule on a per-proposal forecast) and non-myopic (thresholds depending on future-value state). "Dynamic" is not used as a level; "dynamic algorithm configuration (DAC)" names the problem class. A1 is per-instance; A2–A6, A2-U and Track S m* are myopic; Track S π*, π′ and the budget DP are non-myopic. Applies to the manuscript (introduction, problem, setup), PLAN, TECH_ROUTE, C3_DESIGN and the Track S design. |
| R1-SEQ-GATES-PARALLEL (date) | The C3 gate (B.7) and Track S are parallel branches: B.7's outcome does not stop or change Track S, and Track S's outcome does not change B.7, Phase C or R-B. Phase C still requires B.7. Neither outcome authorizes Paper C work. TECH_ROUTE's graph is redrawn accordingly. |
| R1-SEQ-TRACKS-FRAMING-AMEND (date; before any S3e outcome) | Amends R1-TRACKS-FRAMING (30 Oct). The outcome → headline-wording mappings are unchanged. Every "RL arms" clause is replaced: R-B's place is decided only by B.7 and time (R1-BX-D9), whatever Track S finds; a route-A outcome on any channel is recorded as motivation for non-myopic learned control in the follow-up paper, and a no-gain outcome as "not motivated on these nodes at this sensitivity"; no Track S outcome motivates multi-step RL in Paper B. |
| R1-SEQ-RL-WORDING (date) | Wording: R-B is single-step, offline policy-gradient training with a verifiable per-proposal reward and the only arm called RL (R1-BX-D9); the AWR-MLP baseline is single-step offline policy learning on the per-proposal reward and is not called RL; Track P and the offline environment are single-step by design, and the 12-bin action env is superseded for Track P; Stage D measures state-distribution shift only. TRACK_P §1 and §6.4; C3_DESIGN §2 (point 5), §5, §7 and §8; RUNBOOK §6 (DI row), H.7, H.8 and Track H items; TECH_ROUTE's Track H row are corrected as in the proposal §3.4. The `r1/c3/env.py` docstring is corrected only after R1-B2-REPAIR-SCOPE-ACK. |
| R1-SEQ-A7-MOVE (date) | A7 (online RL) and the PLAN §5 secondary "two-step continuation-value rule (Longstaff–Schwartz / FQE)" leave Paper B for the follow-up paper. R1-H8-DEFERRED's trigger becomes "needed by the follow-up paper". A DI violation is reported with the reduction theorem's contrapositive (necessary, not sufficient). The place of the C4 debiased-memory A/B is decided separately. |
| R1-SEQ-BUDGET-FIELDS (date) | The C3 feature `budget_frac_left` and the serialized budget line are redefined from worker runs used/remaining, with a test that both are identical to the current values on every execute-all table; landed before the sweep-2 feature freeze and the Track P template freeze. The D.3 pre-declaration states its LLM-call cap. Every campaign record keeps (or allows deriving) worker runs used/left, LLM calls used/left and proposal slots left. |
| R1-SEQ-TRANSITIONS (date) | Transition-logging contract `docs/r1/TRANSITIONS_SPEC.md` <sha> is adopted. It is met for Track S and the sweeps by a sha256-manifested archive of root, event and leaf records and an offline exporter with a gap list and a ledger-agreement check, with no collector or sweep-runner change and no new pin. Only the D.3 runner carries a logging sidecar, with a normalised-ledger equality test (wall-clock fields excluded), a fail-safe rule and an independent review. |
| R1-SEQ-TRACKS-REV8 (date; before S0.7) | Track S design rev 8 (primary comparison, families, n, Holm rule, placebos, π′ and S0.1 pins unchanged): ladder framing with π′ described as a fork-fitted policy-improvement step; the budget-DP algorithm specified and frozen (slot model, discretisation, keep at m*'s h, value distribution from m*'s S0.7 dev decisions), run as a descriptive secondary on the 30-instance subset only if W binds [and only if the author adopts its pin change from S3e on]; archive and exporter for Paper C records; S0.6 extended with DP oracles as sensitivity only; per-node raw Y with σ_cmp,vary-scaled cross-node summaries; the limits list copied from §10 (only P2+ concentrated calibrated). |
| R1-SEQ-SYNTH (date) | S0.6's synthetic study is extended with an incumbent-interaction world and exact DP oracles, with π′ and the budget DP reported in every world; worlds and target gains are frozen with Track S rev 8 before S0.7 and calibrated as S0.6. Reported as pipeline sensitivity only, never as evidence about the loop, including when used for R1-BX-D10's fallback. The budget channel stays unmeasured unless a non-circular world calibrates. |
| R1-SEQ-THEOREM-CHECKS (date) | The (NI) masking test enters B.3 (M14) on A3 only, with both forecasters given a sufficient encoding of the whole proposal history and no incumbent-dependent feature; the (NF-c) failure is quantified as the share of the horizon consumed by policy-dependent duplicates under A3's deployed rule. Resolves R1-T4-DI-FIX's open item for this check only. |
| R1-SEQ-A2U-REF (date) | A2-U (prior fitted on the B.3 training partition) is an offline reference row in B.3, optionally in D.3; the PLAN §5 random-at-matched-realised-budget baseline is kept offline in B.3. The R1-BX-D8 gate is unchanged. |
| R1-SEQ-ROUTING (date) | Routing of this revision's items: [author to fill; proposed: documents, W1 and W4 to the chat session; W2, W5, W6 to Mac-local (M13, M14); Track S rev 8 review and W3 code to M6]. |
| R1-SEQ-PAPER-C (date) | The Sequential Policy Track, multi-step transition collection beyond the W1 archive and exporter, model-based rollout/MPC, behaviour cloning, offline and online multi-step RL, and multi-step RL of the decision model are scoped to the follow-up paper (`proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md`); no Paper B resources are allocated to them. |
```

---

## 10. Order of edits after adoption

1. Author commits the rows he adopts (§9), with R1-SEQ-TRACKS-FRAMING-AMEND before any S3e outcome.
2. Track S rev 8 document (with the W3 spec and W4 worlds) and its review, before S0.7.
3. W2, before the sweep-2 feature freeze and the Track P template freeze.
4. §3.1–§3.6 document edits on one branch; W1 spec; independent review of each.
5. W4 (CPU), with tests and review; W3 code only if adopted, before S3e.
6. Archive steps added to the operator and HoreKa runbooks; exporter by end of Dec.
7. Manuscript (§3.8) as writing proceeds; W5 and W6 with B.3.

---

## 11. Open questions for the author

| # | Question | Options | Recommendation |
|---|---|---|---|
| O3 | Random matched-budget reference arm in D.3 (comment §6.1; required in PLAN §5) | offline in B.3 only; also in D.3 | offline in B.3 only (free there); reconcile PLAN §5 with D.2/D.3 explicitly |
| O4 | A small MLP rung in the C3 ladder (comment §6.3) | add next to A3/TabPFN; skip | add only if M11 has capacity; it is cheap offline |
| O5 | Budget DP in D.3 | add as an arm; Track S and synthetic only | Track S and synthetic only |
| O6 | Where C4's debiased-memory A/B goes (not asked by the comment) | Paper B appendix (current "or later"); Paper C | Paper C, as this proposal's own suggestion; decided separately from R1-SEQ-A7-MOVE |
| O7 | Working name of the follow-up paper | "Paper C"; other | the author's choice |
| O8 | Routing (R1-SEQ-ROUTING) | as proposed; other | as proposed in the row draft |
| O9 | A masked A5 for W5 | A3 only; authorize a TASL-7 job | A3 only |
| O10 | W3's Track S pin change from S3e on | adopt; synthetic worlds only | adopt only if W binds after S0.5b; otherwise synthetic only |
| O11 | Vocabulary | myopic / non-myopic (proposed); other | myopic / non-myopic |

Revision 1's O1 (rev-8 timing relative to S0.4) and O2 (who implements the collector sidecar) are dropped: there is no collector sidecar.

## 12. What this proposal does not do

It does not change Track S's primary design, any C3 gate number, any authorization, host assignment, budget or date; it does not start any run; and it does not adopt any theory claim before the author's proof check.
