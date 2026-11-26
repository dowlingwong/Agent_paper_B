**AI-assisted (Claude, coordinating chat, 26 Nov 2026). PROPOSAL. It decides nothing; the draft rows in §7 become
decisions only when the author signs them.**

# Paper B: aligning the research goal, the evaluation metrics and the claimed contribution

Written after two external reviews of the 23 Nov manuscript build (`papers/r1` @ `1f89cb48`), which the author
forwarded on 26 Nov. Checked against published `main` @ `a1597f70`. No label, test or evaluation file was opened.

## 1. State when this was written

Nothing below has happened yet, so every change in §4 can still be declared in advance:

- the preregistered gate (R1-SWEEP2-PREREG, gate v3.1) has not been read;
- no arm is frozen (the arms-frozen record is due by 20 Dec, R1-ARMS-FREEZE-CUTOFF);
- no D.3 campaign has run, and the D.3 pre-declaration is an unsigned draft (revision 3, branch
  `mac-d3-predecl-20261122`, not on `main`).

## 2. The mismatch

The paper works at three levels.

| Level | Question | Statistic | Where it sits today |
|---|---|---|---|
| 1 Forecast | can the increment distribution of a proposal be predicted? | ranked probability score, calibration | supporting |
| 2 One-step decision | do better forecasts give better execute/keep decisions on logged proposals? | offline one-step utility, gap closed against A2 at price g = 0.1 σ_node | **the single preregistered primary read** |
| 3 Campaign | does the loop reach a larger audited gain at the same budget? | D.3's Y at W = 20 worker runs and 80 LLM calls | D.3a unconditional; **D.3b only if the level-2 gate passes** |

The introduction and title state a level-3 goal ("the largest real gain per run under a fixed budget"). Three points
do not line up with it.

- **M1, gatekeeping.** The level-2 gate decides whether the level-3 experiment of the learned arms runs (R1-D3-MIN).
  The gate's simulated power is 0.36 at effect size 0.3, and 0.26 for T1 nodes with six instances (R1-BX-D8-V3-B).
  A failed gate would therefore leave the paper unable to say anything about learned control in the loop, in either
  direction.
- **M2, estimand.** The offline utility prices a run at 0.1 σ_node and does not reuse a skipped run. In the loop a
  skipped run is spent on the next proposal, and a decision changes what the manager sees next. Section 2 of the
  manuscript says that offline utility and campaign gain have no guaranteed sign relation. Track S supports the
  concern from the other side: at this price the constant-prior screen was inert on both pilot nodes (V* − g of
  2.6 to 4.1 σ_node; every skip was a rule-layer duplicate; R1-TRACKS-STOP4-END), so on T0 the levers that act are
  de-duplication and the keep threshold.
- **M3, contribution order.** The contribution list leads with C1 (a measurement the literature already has,
  R1-C1-POSITION), then C2 (a classical threshold, a selection-bias inequality and a conditional reduction theorem),
  then C3 offline. The closed loop, which answers the title's question, comes last and is half conditional.

There is also a mismatch of effort. The closed loop is the least advanced track. Its pre-declaration is unsigned; the
screening measurement that must precede the signature (R1-SCREEN-MEASURE) has not run; of the units in the draft's
§12, G1 (runner), G3 to G8 (FIXR3, EGATE, LADDER, the Y audit, the outcome table, the run accounting) are missing; no
agent has this work in its queue. Nothing on `main` has touched it since 23 Nov.

## 3. What the reviews did not credit (already in the plan)

| Review point | What exists |
|---|---|
| "tasks are single-parameter HPO" | True of T0 only. T1 has eight GPU nodes from three public suites with code-level diffs, in the same gate (tier as a stratum), with leave-one-suite-out; up to four more nodes are being screened (R1-T1-NODE-EXPANSION). On T1, A5 reads the diff text (D7-DIFF B) and A3 does not. |
| "no closed loop without the gate" | D.3a (six rule arms) is unconditional (R1-D3-MIN, R1-MINSUB-CHOICES (4)). |
| "saved budget is not reused" | True offline only. In D.3 a skip charges no worker run and the manager is asked again, up to 80 calls. |
| "no noise-aware-only arm" | A1 is the index policy without the rule layer. Only a rule-layer-only arm is missing. |
| "test tasks generated after the freeze" | D.3 uses 18 new instances per node, disjoint from every sweep and split file. |
| "greedy control ignores information value" | This is the subject of Paper C (R1-PAPERC-REFRAME, census first). Paper B makes no multi-step claim (4 Nov). |
| "power is low" | Disclosed in the manuscript with its qualifiers (PRE-POWER A). |

## 4. Proposed changes

The preregistration, the gate code, the split, the release order and every signed note stay as they are. All changes
are to D.3 (not yet declared), to the wording of the claims, and to the order of work.

| # | Change | Cost | Recommendation |
|---|---|---|---|
| A1 | **Claim order.** The headline question is level 3: at a matched budget, which control decisions raise the audited gain of a campaign, and by how much. The gate stays the preregistered test of the level-2 claim and is read once. Both families are reported whatever they show. | wording | adopt |
| A2 | **D.3b runs whether or not the gate passes.** A3 and A5 as frozen in the arms-frozen record. The D.3b family gains A5 − A3 (language model against tabular). | 7.9 GPU-h on the realised sweep-2 basis, 40.2 on the layout basis, plus the sidecar (draft §11); no schedule change, since D.3b waits for the arms-frozen record anyway | adopt |
| A3 | **Arm A0R in D.3a**: the default keep rule with the rule layer. With A0, A1, A2 it gives the 2 × 2 of rule layer × index policy, so de-duplication and noise-aware decisions are separated. Sweep 1 had 3,274 duplicates among 4,999 replayed proposals. | about 2.2 GPU-h realised, 11.3 layout; a small controller unit | adopt |
| A4 | **Secondary outcomes of D.3, descriptive:** the budget curve Y(w) at w = 5, 10, 15, 20; compute per campaign (worker seconds, LLM calls and tokens, proposer GPU-seconds, controller inference seconds, wall-clock); runs-to-match A0; mechanism counts (duplicates proposed and executed, rule skips, value skips, keeps, distinct configurations, last improving run). | CPU audits only (at most four times the Y audit, which is 43 min at 16 workers for D.3a); logging fields and analysis code | adopt |
| A5 | **Offline–online agreement, descriptive:** per node and arm, the gate's per-node utility beside the closed-loop Y, and the rank agreement of the arms. Uses only outputs the preregistered analysis already writes. | analysis code | adopt |
| A6 | **Learning against proposal complexity, descriptive:** A5 − A3 and A5 − A2 by tier (T0 single-parameter edits, T1 code diffs), from the per-node and per-tier tables of preregistration §7. If it needs any read beyond those tables, it goes into a signed amendment before the arms-frozen record. | analysis; possibly one short amendment | adopt |
| A7 | **Classical configuration as the proposer on T0, reference rows:** random search with de-duplication, and SMAC3, on D.3's instances at W = 20, audited as Y is. Outside the Holm families. | CPU only; a unit of a few days with its review | adopt as optional under the 3 Jan rule |
| A8 | **Closed loop on T1, descriptive (D.3c):** the three pilot nodes (measured liveness 0.62 to 0.82 and throughput in G.4b), new instances, arms A0, A2, A3, A5. | about 0.3 GPU-h per campaign from G.4b (9 campaigns in 2.46 GPU-h) plus the audit; the TASL pair is free once the G.5 labels are complete; the engineering is not scoped | ask for a one-day scoping memo; decide by 10 Dec |
| A9 | **Order of work.** The D.3 chain starts now: merge and run the screening measurement, revise and sign the pre-declaration, build G1 and G3 to G8. | agent time | adopt |

Why A2 is legitimate. The gate is unchanged and unread. Whether D.3b runs was fixed by a PLAN row (R1-D3-MIN) and the
RUNBOOK, not by the preregistration. Changing it before any outcome exists is a design decision, and it is recorded
with its date and reason in the deviations table.

Why A3 matters. If A2 beats A0 in the loop mostly through de-duplication, the paper must say so; a 2 × 2 is the
cheapest design that can.

A7's risk, stated in advance. On single-parameter tabular tasks a classical method may match or beat the LLM loop.
The paper then says that T0 is a controlled testbed where the decisions can be audited cheaply, and that an LLM
proposer is needed where edits are code (T1). It is better to measure this than to have a reviewer assert it.

## 5. Not proposed for this submission

| Review suggestion | Why not now |
|---|---|
| A new tier T2 (architecture and algorithm changes) | Cut on 22 Nov (R1-SUBMISSION-CUTS). T1 already carries code-level diffs. |
| Exploration-aware and information-aware controllers; a score with an information term | A new method and the core of Paper C. At g = 0.1 σ_node the constant-prior screen makes no value skip on T0 (Track S), so an exploration floor on A2 would change nothing there. A4's value-skip counts and A5's agreement table show whether the learned arms' skips cost gain; that result decides the follow-up. |
| Bayesian optimisation and successive halving as further baselines | SMAC3 and random search answer the question; successive halving needs a fidelity axis the nodes do not have. |
| A decision model with gain, information and cost heads | After A5 against A3 is known (the review says the same). |
| More theory on the two reduction conditions | None is planned. |
| Changing the gate, its price or its eligibility rules | Never after preregistration. |

## 6. What the paper says under each outcome (declared now)

| Closed loop, rule arms | Closed loop, learned arms | Offline gate | Headline |
|---|---|---|---|
| A2 > A0 | A5 or A3 > A2 | pass | learned control raises audited gain at matched budget; the decomposition says how much each part buys |
| A2 > A0 | A5 or A3 > A2 | fail | the same headline from the closed loop; the gate result is reported as measured, with its power; the offline–online disagreement is a finding |
| A2 > A0 | no gain over A2 | pass | one-step gains do not carry into the loop; A4 and A5 of §4 say where they are lost |
| A2 > A0 | no gain over A2 | fail | noise-aware rule control is enough at this task complexity; effect sizes and intervals bound what learning could add; the tier table says whether that changes with code-level edits |
| no gain over A0 | any | any | the measured negative: C1 and the theory stand, and the loop is shown not to be limited by its keep and screen decisions on these tasks. Not an ICML submission in the present form. |

## 7. Draft rows (for the author; text may be edited before signing)

| ID | Decision |
|---|---|
| R1-ALIGN-OUTCOME | **The paper's headline question is the campaign-level one, and its answer is the closed loop** (author, 26 Nov 2026, after two external reviews of the 23 Nov manuscript build; decided before the gate read, before the arms-frozen record and before any D.3 run). Question: at a matched worker-run budget and LLM-call cap, which control decisions raise the fresh-seed audited gain of a campaign, and by how much. Its outcome is D.3's Y. The preregistered offline gate (R1-SWEEP2-PREREG, gate v3.1) is unchanged and is read once as preregistered; in the paper it is the confirmatory test of the one-step claim (a learned forecast improves the one-step decisions on logged proposals against A2), and it no longer decides which closed-loop arms run. The gate's Holm pair and D.3's contrast families answer different questions, each keeps its declared error control, and both are reported whatever they show. The outcome table of `proposals/GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md` §6 is the declared reading. R1-SUBMISSION-MIN's four parts stay; `CURRENT.md` §1 and the manuscript's contribution list follow this row, and the change is listed in the deviations table. |
| R1-D3B-UNCONDITIONAL | **D.3b runs whether or not the gate passes.** Amends R1-D3-MIN ("D.3b (learned arms; only if the gate passes)", "If the gate does not pass, D.3b is not run") and, for D.3b only, the RUNBOOK's "only if B.7 passes": A3 and A5, exactly as frozen in the arms-frozen record, run in closed loop on D.3a's instances and seeds after that record is committed. The D.3b family gains the contrast A5 − A3. A6 stays as R1-D3-MIN states. The D.3 pre-declaration is revised for this (it sets the multiplicity of the enlarged family) and is signed before any D.3 run. Projected proposer cost: 7.9 GPU-h on the realised sweep-2 basis, 40.2 GPU-h on the layout basis, plus the sidecar (pre-declaration draft §11). |
| R1-D3-DECOMP | **One arm is added to D.3a: A0R, the default keep rule with the rule layer** (a proposal the rule layer marks as a duplicate or a detectable no-op is skipped and charged no run; every other proposal is executed once and kept iff Δ̂ > 0; no screen, no verify). With A0, A1 and A2 it forms the 2 × 2 of rule layer × index policy. Contrasts added to the D.3a family: A0R − A0 and A2 − A0R. The arm reads no label and gets no offline test read by this row. |
| R1-D3-OUTCOMES2 | **Secondary outcomes of D.3, descriptive and without a verdict, written into the pre-declaration before any run:** (a) the budget curve Y(w) for w = 5, 10, 15, 20: the incumbent after the w-th charged worker run, audited as Y is; (b) compute per campaign: worker runs and worker seconds, LLM calls and tokens, proposer GPU-seconds, controller inference seconds, wall-clock time; (c) runs-to-match: per node, the smallest w at which an arm's mean Y(w) reaches A0's mean Y(20); (d) mechanism counts per campaign: duplicates proposed and executed, rule skips, value skips, keeps, distinct configurations executed, the last charged run that improved the audited incumbent; (e) offline–online agreement: per node and arm, the gate's per-node utility beside the arm's closed-loop Y, with the rank agreement of the arms, from outputs the preregistered analysis already writes; (f) A5 − A3 and A5 − A2 by tier from the per-node and per-tier tables of preregistration §7 (a read beyond those tables needs a signed amendment before the arms-frozen record). The primary Y at w = 20 and its contrasts are unchanged. |
| R1-D3-HPO-REF | **Reference rows, optional under R1-SUBMISSION-MIN's 3 Jan rule: classical configuration methods as the proposer on T0.** Random search with the rule layer's de-duplication, and SMAC3, each in place of the manager on D.3's instances with W = 20 worker runs; the final incumbent is audited as Y is. The unit states each node's configuration space and its review checks it against the edits the proposal schema admits. Descriptive, outside the Holm families. The result is reported whichever way it falls. |
| R1-D3-ORDER | **The D.3 chain starts now and is the first claim on desk time after the expansion G.1b note and the G.5 note.** Order: (1) merge `mac-screen-measure-20261123` and run the screening measurement on deepthought CPUs after its smoke and the author's signature (R1-SCREEN-MEASURE-CHOICES); (2) revision 4 of the D.3 pre-declaration with the rows above, reviewed until accepted, then signed; (3) the units G1 and G3 to G8 of the draft's §12 and A0R, each tier E; (4) the per-arm smoke on the HTCondor GPU model D.3 will use. If the NEMO2 H200 is still out when (4) is due, another GPU model of the pool is measured instead, as the draft's §2 allows. A one-day scoping memo for a descriptive T1 closed loop on the three pilot nodes is written in parallel; the author decides on it by 10 Dec. |

## 8. Open points

- Who revises the pre-declaration (it was drafted in the other chat session): proposed, the Mac agent, as one reviewed
  unit, so that one hand holds the file.
- The manuscript is restructured after the rows are signed: the level-3 question first; the decomposition as the main
  result table; the theory cut to what derives the rule and states its scope; the audit and preregistration procedure
  moved to the appendix. A new title is the author's choice.
- A2 puts the A5 sidecar image (draft §13 item 16) on the path of D.3b in every case, so it needs an owner now.
