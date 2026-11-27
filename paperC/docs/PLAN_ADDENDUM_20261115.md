# Paper C plan — addendum of 15 Nov 2026 (to revision 2 of 5 Nov)

**AI-assisted (Claude, chat session), written 15 Nov 2026 at the author's request.** It amends `proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md` (rev 2, "the plan") and is read together with it. Where they conflict, this addendum controls. Like the plan, it is a working plan. Real-node runs need their own runbook, review and authorization (§C).

Changes:
- **A.** Single-teacher on-policy distillation (OPD) is added to Paper C as LM route M4. The author decided on 15 Nov that it belongs in Paper C, not Paper B.
- **B.** The plan is adjusted to Track S ending at STOP 4 before EVIDENCE (PLAN §10 R1-TRACKS-STOP4-END, R1-TRACKS-STOP4-CONSEQUENCES, 15 Nov).
- **C.** Paper C no longer waits for Paper B's submission (author, 15 Nov); see §C.
- **E.** The response to Track S STOP 4 is proposed in `proposals/PAPER_C_REFRAME_AFTER_TRACKS_STOP4_20261115.md`: acceptance and evaluation control as the core, broadening to expensive GPU runs, and a headroom census first. It needs author rows R-C1 and R-C2.

---

## A. Route M4 — single-teacher on-policy distillation

### A.1 Why Paper C and not Paper B

In Paper B the decision model's belief is read out in one forward pass as a 12-bin distribution, not generated token by token. With nothing for the student to generate, "on-policy" and "off-policy" distillation are the same thing: plain logit distillation on fixed inputs.

In Paper C the policy acts over a whole campaign. The states a student controller visits depend on its own past actions: the budget path, which edits were kept, and the proposer's reaction to the keeps. They differ from the behaviour-mixture states the offline data cover. Training on the student's own state distribution is therefore a real design variable here. At the decision level, OPD is DAgger (Ross et al. 2011) with soft teacher targets.

### A.2 Two variants

| Variant | Student | Teacher | States | Loss | Tier |
|---|---|---|---|---|---|
| **M4a — loop-level OPD** | the action/advantage head of the LM decision model (Kev-0.8B; Qwen3.5-0.8B-Base control), or a small MLP on E-SYN | the frozen dev-selected best multi-step policy of the core ladder ({N6, R0, R1}; M2 if it exists). LM variant: Kev-4B after M1/M2 → Kev-0.8B | states visited by the student's own campaigns on **training** instances | per eligible decision, divergence between student and teacher action distributions (reverse KL primary, forward KL as sensitivity; declared before training). The belief head stays trained only by its proper score (belief/action decoupling, plan §9.2) | **proposed for the core version as a conditional item** (gate A.4); the author decides (open item P10) |
| **M4b — token-level OPD** | a text-generating controller (reason-then-act; the sequential LLM self-control arm of plan §13) | a larger model **with the same tokenizer** (Qwen3.5 family; the pick only if its tokenizer is identical, to be verified) | the student's own sampled tokens, at states from SPT-2/3 logs or from student campaigns | per-token reverse KL on the student's tokens | extension |

**Information principle (plan §3.2).** The teacher sees the same legal state as the student. A teacher with privileged inputs (audit values, future fields, fork outcomes at test time) is allowed only as a labelled *privileged-teacher* ablation.

**Difference from N8 (AggreVaTe-style, plan §7.1).** N8 labels the learner's states with charged fork rollouts, so the labels are rollout returns. M4a labels them with a frozen teacher policy at the cost of one small-model inference. Its labels are only as good as the teacher at states the teacher may not have been trained on (A.5).

### A.3 Comparisons (secondary family, declared before SPT-5)

| Comparison | Isolates |
|---|---|
| M4a vs **M1** (same teacher, same student; M1 is distillation on logged behaviour states) | the effect of training on the student's own state distribution |
| M4a vs **M3** (fork-grouped policy gradient on terminal audited Y), matched in new worker runs + LLM calls + audits | dense per-decision teacher signal vs sparse terminal-return RL at equal interaction. This is the central argument of the 2026 OPD/MOPD reports, tested in a governed loop |
| M4a vs its **teacher** | how much of the teacher's gain a smaller student keeps |
| Kev-4B → Kev-0.8B (M4a, LM) vs Kev-0.8B M1 | the on-policy effect for LM controllers |

Q3's confirmatory family (plan §2, §11.3) is unchanged. M4 results never enter it.

### A.4 Gate

M4a runs only if all of these hold:
1. the teacher beats N1 on **dev** campaigns. Without headroom there is nothing to distil;
2. SPT-4 support targets hold for the teacher's training data;
3. the cost projection (A.6) fits an authorized budget.

M4b additionally needs the plan §9.1 gates.

### A.5 Risks

- **Teacher extrapolation.** The teacher is itself a learned value model, and it is queried at the student's states, which may lie outside its training support. Report the teacher's support diagnostics (plan §6.1) at the student's visited states. Decisions in unsupported clusters are flagged and reported.
- **Compounding.** Teacher errors along the student's trajectory compound across a campaign. Monitor the student's dev return per update batch and roll back on collapse (plan §9.4).
- **Calibration.** The belief head must keep its Paper B metrics (ECE, width ratio). M4 trains the action head only.

### A.6 Cost (rough, recompute after SPT-1)

One student campaign costs about 40 proposer calls and yields about 14–20 teacher-labelled decisions. Teacher queries are small-model inference and cost almost nothing. M3 needs about 8 continuations of about 20 calls per root for one group-relative signal. Per supervised decision, M4a is therefore roughly an order of magnitude cheaper than M3. This is an estimate to be replaced by SPT-1 numbers, not a measured figure.

### A.7 Where it is built

On E-SYN first (BUILD_LIST item B12, runbook phase P10): an MLP student and teacher, M4a vs M1, in a world where the student's actions shift the state distribution (keep feedback, P2±). The LM version uses Track P's training loop (`r1/c3/train/`) on TASL-7 or HTCondor, after Paper B's needs.

---

## B. Consequences of Track S STOP 4 for Paper C

**Facts** (PLAN §10 R1-TRACKS-STOP4-END, from the two-node S0.5 summary):
- Track S ended at STOP 4, before EVIDENCE. A2-U failed the S0.5 calibration gate on both E-T0 nodes. Coverage of the 80 % interval in the "0 prior observations" stratum was 0.538 on digits_mlp and 0.368 on tabular_mlp.
- E1 screening was inert. On every eligible non-duplicate E1 decision, V\* − g was 2.58–2.61 σ_node (digits) and 4.04–4.06 σ_node (tabular). No decision lay within ±0.5 σ_node of the run price or of the static threshold. All E1 skips were rule duplicates.
- The two pilot policies took identical actions.

**What changes in the plan:**
1. **Q1 hypotheses on E-T0** (plan §2) can no longer be "fixed after Paper B's Track S outcome", because there is none. They are fixed from E-SYN and SPT-1 before any SPT-2 data. Paper C's Q1 on E-T0 is a first test, not a replication of Track S.
2. **Inherited Track S numbers** (binding shares, σ_D, flip rates, channel contrasts; plan §1) are pilot quantities only. They may inform power planning but are never cited as evidence.
3. **Decision relevance is a precondition.** With the run price g = 0.1 σ_node and these forecasters, the E-T0 execute/skip decision has no decision-relevant states, so E1 headroom is zero by construction. SPT-0 therefore adds a **decision-relevance check** (BUILD_LIST item B10):
   - Before any SPT-2 collection on a node, the declared belief, price and budget must put a declared minimum share of eligible decisions near the threshold (the share and band are fixed in SPT-0).
   - Otherwise round A on that node is reported as "no decision-relevant states" and not run.
   - The keep/discard (E2) channel and binding budgets remain candidates and get the same check.
4. **A2-U** stays a reference row on E-T0 only, disclosed as having failed calibration. The common frozen C3 belief (plan §7.0) is unchanged.
5. **Track S engineering** (fork collector, arm-override hook, worlds, oracle, `schema.py`) is still the starting point for SPT. It lives on `trackS-ops-20261030` (at `fab88fc` on 15 Nov), not in the canonical line. Paper C ports from a recorded pin and does not import from that branch.
6. **Paper B's framing** is now "noise-aware DAC and when it reduces to one-step decisions", supported by theorems and synthetic controls; the RL arms are not required (R1-TRACKS-STOP4-CONSEQUENCES (1)). Real-loop sequential evidence is Paper C's to provide.

---

## C. No waiting for Paper B's submission

**The author removed the plan's rule "no Paper C run before Paper B's submission (10 Jan 2027)" on 15 Nov.** This replaces the plan's Status paragraph and the "Nov 2026 – 10 Jan 2027" row of plan §14. Paper C work, including runs on real nodes, may start now. It follows the same practice as Paper B:
- every real-node phase gets its own runbook, an independent review, and an author authorization before it runs;
- seeds come from the Paper C registry (BUILD_LIST B2);
- hosts follow the PLAN host rows. HoreKa 2 and the ETP HTCondor GPUs are the natural Paper C hosts. Paper C uses TASL-2 and TASL-7 only where an author row allocates them;
- the build phases P0–P10 themselves are CPU-only and change nothing outside `paperC/`.

## D. Status of the 5 Nov positions

The author's positions of 5 Nov were: proposer of record = the exam winner, a core version for the first submission, and δ as in plan §11.3.
- On 15 Nov the author asked for them to be written into PLAN. R1-PAPERC-PROPOSER and R1-PAPERC-DELTA are recorded in `docs/r1/PLAN.md` §10 (15 Nov section), together with R1-PAPERC-OPD, R1-PAPERC-NOWAIT and R1-PAPERC-HOME.
- **R1-PAPERC-CORE is held back.** Its 5 Nov content (Q1 confirmatory on E-T0 in round B) is what Track S STOP 4 undercuts, so it is rewritten after the reframing decision (R-C1).

New open item **P10:** promote M4a into the core version as a conditional item (gate A.4)? Recommendation: yes, because it is the cheapest on-policy method and answers a clear question, and its gate keeps it from consuming budget when there is no headroom.
