# Paper B: recommendations behind the rows of "22 November 2026 (d)", and three open proposals

*AI-assisted: written by the chat-session Claude on 22 Nov 2026. No human review. This file records what the chat session recommended to the author on 22 Nov, so that the rows R1-SUBMISSION-MIN to R1-C1-POSITION can be compared with it. It is not a decision; the rows are. It contains no quotation of the author.*

## 1. What the review of 22 Nov found

The review covered five questions: novelty and rigour, the fit of the five research directions, the split between Paper B and the follow-up paper, the planning documents and manuscript, and the experiments.

1. **Novelty.** C1 is no longer a first measurement (`inputs/NOVELTY_SWEEP_PART3_20261122.md`). The statistical-gate family is crowded. What remains distinct is the combination: a rule that weighs audited gain against a run price, screening before a run is spent from a per-proposal forecast, theory for a ledger-dependent proposer, and a learned forecast compared with a theory-derived index policy at matched compute.
2. **Framing.** The learned object is a forecaster and the policy is a rule derived from it. The reduction of the control problem to one-step decisions is a conditional theorem. Paper B does not use "RL" for anything it does.
3. **Schedule.** With the gate read at about 15 Dec and submission on 22 Jan, the plan as written (T1 and T2 closed loop, API proposer, aggregation round, several optional arms) did not fit. The T1 table was the critical path.
4. **Power.** The gate's simulated power is low (0.36 at effect size 0.3). The paper has to stand if the gate does not pass.
5. **Theory.** Only three propositions carry a recorded author check. An earlier AI audit had found two propositions wrong.
6. **Manuscript.** The manuscript was a skeleton last edited on 28 Oct.
7. **Process.** The record held about 600 review files, 340 reports and 120 proposals; STATUS had no entry after 16 Nov. Every unit, whatever its weight, went through the same review procedure.

## 2. What was recommended

1. Define a minimum submission version of four parts (C1 from the audited sweeps; C2 with checked statements; C3 offline by the preregistered gate; a closed loop on T0), and treat everything else as optional with a fixed last date.
2. Bound the wait for T1 labels with a date for the arms-frozen record, inside what the frozen preregistration allows (one primary read; the T1 node set is the set labelled at the freeze).
3. Split the closed loop into rule arms, which need no gate result, and learned arms, which do.
4. Cut T2, the API proposer, closed loop on T1, and the optional arms and rounds named in R1-SUBMISSION-CUTS.
5. Keep the full procedure for evidence-bearing units and lighten it for support work and drafts.
6. Keep one short current-state document.
7. Start the manuscript now, with results text prepared for both gate outcomes.
8. Reposition C1 and narrow the decision-focused-training claim.

The independent review `reviews/MINSUB_PLAN_REVIEW_20261122.md` then found that the first wording of items 2, 3 and 5 conflicted with frozen records; the rows were corrected.

## 3. Three proposals (decided on 22 Nov in R1-MINSUB-CHOICES)

*P1 is decided with a changed order (item 1 of the row): the TASL pair has one worker slot, so no node can have its own card; the order is one cheap node per other suite, then `autoresearch_fixedtokens`, then the rest. P2: the quota page was read on 22 Nov and its rules are in item 2. P3: the arm is added to D.3a as the Ladder margin rule, without a screen (item 4). The text below is the proposal as first written.*

**P1. Order of the G.5 label runs.** The leave-one-suite-out analysis STOPs if any suite has no labelled T1 node (R1-BX-D8-CONFIRM-V31), and `autoresearch_fixedtokens` is the only node of its suite and the longest (about 138 of 305 GPU-h, R1-G5-DECISIONS). Proposal: start `autoresearch_fixedtokens` first and keep it running on its own card, and within each of the other two suites run the cheapest node first, so that each suite has a labelled node as early as possible. The opposite order (autoresearch last) protects the node count of the aggregate gate but risks the suite-level test.

**P2. ICML 2027 submission quota.** On 22 Nov the quota page (`icml.cc/Conferences/2027/ReciprocalReviewingAndSubmissionQuotas`) could not be opened; a search excerpt suggested a limit for author teams without prior publications at listed venues. Proposal: the author reads the page before a second ICML submission is planned, and settles the author list with it in mind.

**P3. A static threshold arm tuned on dev campaigns.** A reviewer will ask whether a pair of constants (screen threshold, keep threshold) found by direct search on dev campaigns does as well as the theory-derived constants of A1 and A2. Proposal: check whether the ladder already contains such an arm. If it does not, adding one to the offline tables needs it in the arms-frozen record and inside the preregistration's secondary scope, or a signed amendment; adding it to D.3a needs it in the D.3 pre-declaration. The follow-up paper's synthetic study found that a tuned static rule closes most of the gap to the optimum in its short-budget world (`paperC/docs/reports/ESYN_SCALING_HEADROOM_20261122.md`, on a Paper C branch), which is why the question matters.
