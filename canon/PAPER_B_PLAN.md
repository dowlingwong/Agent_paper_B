# Paper B (route R1): the plan as it stands

**Execution snapshot, 27 Nov 2026.** [PLAN §10](../docs/r1/PLAN.md#10-open-decisions) and the published launch
notes govern execution (R1-CANON-FOLDER). The [live queue](https://github.com/dowlingwong/Agent_paper_B/blob/coord/coordinator/STATE.md)
tracks current work. Steps start when their prerequisites are complete and reviewed (R1-STEP-ORDER).
The gate is unread, arms freeze is pending, and the campaign results are still to be collected.

## 1. Question and claims (R1-ALIGN-OUTCOME)

**Question.** At a matched worker-run budget and LLM-call cap, which control decisions of a governed autoresearch loop
raise the fresh-seed audited gain of a campaign, and by how much?

| Claim | Content | Evidence |
|---|---|---|
| Loop (headline) | Rule and learned control against the default loop at matched budget; what de-duplication, noise-aware decisions and a learned forecast each buy | Closed loop D.3 on T0: D.3a rule arms, D.3b learned arms (always run), D.3c on three T1 nodes (descriptive) |
| C3 offline | A learned per-proposal forecast improves one-step decisions on logged proposals against A2 | The preregistered gate, read once (R1-SWEEP2-PREREG, gate v3.1) |
| C1 | Control errors of the default keep rule: false keeps, missed keeps, the winner's curse, wasted runs. Supporting, not a first measurement (R1-C1-POSITION) | Fresh-seed audits of sweeps 1 and 2 |
| C2 | The one-step rule under noise for a ledger-dependent proposer, and the conditions under which it is globally optimal | Main-text statements pass the independent proof check and the coordinator's spot check (R1-PROOF-POLICY) |

Report the offline gate and both D.3 contrast families whatever they show. The declared outcome readings are in
[D.3 rev 4 §7.4](../docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md). No multi-step claim is
made; that is Paper C. Wording rules: the learned object is a forecaster, the policy is a derived rule, the term "RL"
is not used (R1-BX-D9).

### What this evidence establishes for Paper C

The exact reduction in C2 gives Paper C its one-step reference. D.3 tests the value of deploying one-step
control under a matched hard budget. Paper C tests the value of modeling how current actions change the
remaining search. A3 and A5 forecast the immediate audited increment. Supervised fine-tuning or a stronger
teacher can improve that forecast and are implementation choices. An offline gate pass, a D.3 win, and
offline–online agreement each answer their own question.

The two T0 sweeps provide proposals, ledgers and fresh-seed audit labels for current-candidate increments.
They support immediate forecasting, an audit-based one-step reference, and diagnostics of predictive
history or near-threshold decisions. Paper C needs newly observed continuations from alternative actions
to estimate their downstream effects. Its [plan](PAPER_C_PLAN.md) specifies that contrast and the handover.

The [next-phase runbook](../docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md) sets the writing and
compute handoffs for these comparisons.

## 2. Design

| Part | Content | Rows |
|---|---|---|
| T0 | Eight CPU nodes, single-parameter edits; seven in the primary set, `openml_wdbc` a sensitivity row. Two sweeps (7B manager; `gemma4_31b` thinking off), 18 instances per node, W = 20 | R1-MAIN-PROPOSER, PRE-WDBC |
| T1 | Eight GPU nodes from MLAgentBench, MLGym and autoresearch, with code-level diffs and 12 instances per node. Eligible expansion nodes join G.5 through an addendum after G.1b determinism PASS. For the expansion, the MLGym nodes enter the arms and primary gate and the 1GC nodes are reported separately. | R1-T1-D21-SCOPE, R1-STEP-ORDER, R1-G5-S9 |
| Arms | A0 default; A1 index policy; A2 A1 + rule layer; A3 tabular forecaster; A4 LLM self-assessment; A5 fine-tuned small LM; A6 after the gate only | R1-C3 (ladder), R1-ARMS-DECISIONS |
| Offline gate | A3 and A5 against A2: IQM of gap closed and probability of improvement, Holm; split 1/3 : 1/6 : 1/2; price 0.1 σ_node; simulated power 0.36 at effect 0.3 (0.26 for T1 × 6) | R1-BX-D8-V3-A/B, R1-BX-D8-CONFIRM-V31 |
| D.3a | T0, seven nodes × 18 new instances, W = 20, 80 LLM calls; arms A0, A0R, A1, A2, FIXR3, EGATE, LADDER; Y = audited final-vs-start gain / σ_node, K = 10 | R1-D3-MIN, R1-MINSUB-CHOICES (4), R1-D3-DECOMP |
| D.3b | A3, A5 as frozen, on D.3a's instances; contrasts against A2, A0 and A5 − A3; not conditional on the gate | R1-D3B-UNCONDITIONAL |
| D.3c | T1 pilot nodes `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`; A0, A2, A3, A5; descriptive | R1-D3-ORDER |
| Secondary outcomes | Budget curve Y(w), compute per campaign, runs-to-match, mechanism counts, offline–online agreement, learning by tier | R1-D3-OUTCOMES2 |
| Reference rows | Random search with de-duplication and SMAC3 as the proposer on T0 | R1-D3-HPO-REF |

Cut from the submission (R1-SUBMISSION-CUTS): tier T2, the API proposer, arm R-B, the aggregation round, the
debiased-memory A/B, the information-matched TabPFN comparison. Optional work enters if it is complete and reviewed
when the four required parts are, and never delays them (R1-STEP-ORDER).

## 3. State by track

| Track | State | Next |
|---|---|---|
| T0 labels | Both sweeps audited; label tables frozen; train/dev released (sweep 2: 850/422; sweep 1: 593/276); A3's T0 run reviewed | — |
| T1 noise floors | G.1b sealed for all eight nodes; cross-host checks xc2 and xc3 PASS (seven nodes may audit on TASL-7) | — |
| T1 pilot | G.4b PASS: 126 of 180 proposals ran (0.70); liveness 0.62 to 0.82 per node | — |
| T1 labels (G.5) | The author signed rev 13 and settled P10, P11 and S9. The Student-t scope and scale are signed in R1-G5-TAILS-CONSUMERS. Pilot basis passed on TASL-2 and the houseprice CPU-set fix is merged. | Review the sd-matched assembly path, complete the remaining note checks and publish G.5. Review and bind the downstream consumers before arms freeze. |
| Expansion nodes | Kit c1 and the launch note are published. ETTh1 is sealed and Titanic, MetaMaze and Forest Cover are running in the latest compute report. | Seal and assemble the remaining results, then add eligible nodes to G.5 under S9. |
| Decision models (P.4) | Direct launcher and Ada host template merged. The Ada environment smoke passed. | Confirm the launch account, fill and review the Ada host configuration, then run the probe on one RTX 6000 Ada. The phase-1 note follows the probe. |
| Gate | Preregistered and unread. | Review the Student-t consumer amendment, freeze the arms, then perform the one authorised read. |
| Closed loop D.3 | Rev 4 and verify-seed option A are signed. Several controller units are merged. | Finish G1/G6, the constants and the verify-seed check. Run the HTCondor preflight in parallel, then the per-arm smoke and the stage-specific authorizations. |
| Theory | Use main-text statements that pass R1-PROOF-POLICY. | Complete the remaining checks before the gate read. |
| Manuscript | The matched-budget decomposition leads `papers/r1`. Both gate drafts are available. | Insert authorised effect estimates and intervals, and attribute supported gains to the component contrasts. |

## 4. Order of steps (R1-STEP-ORDER)

No calendar date decides anything. A step starts when the steps it depends on are complete and reviewed; no step is
cut, shortened or reordered to meet a date.

**To the gate**

1. Complete and seal expansion G.1b. A node with determinism PASS joins G.5 through an addendum under S9.
2. Review the sd-matched G.5 assembly and finish the note checks. Publish the signed authorization and collect the labels.
3. Complete the Ada P.4 probe, sign the phase-1 note and run training. Prepare the probe in parallel with G.5.
4. After labels complete for the T1 set, publish the train/dev release. Apply the reviewed target consumers to
   SFT, training and fitting as appropriate.
5. Freeze the trained and calibrated arms after the reviewed preregistration amendment. Read the gate once (B.7).

**To the closed loop** (beside 1 to 5)

6. Merge the reviewed screening fix, repeat the smoke, obtain the launch signature and run the screening measurement.
7. Complete the reviewed G2 constants and verify-seed check, then freeze and publish the signed D.3 rev 4.
8. Finish the runner and audit. Check an ETP L40S or TOpAS A100 through HTCondor in parallel with implementation,
   then run the per-arm smoke on a matched GPU layout.
9. Launch D.3a under its authorization and D.3b under its authorization after arms freeze, whatever the gate verdict.
   D.3c may enter after G.5 and arms freeze under its own approved design and authorization.

**To the paper**
10. Test release rows and the post-freeze reads; the manuscript with the numbers. The submission version is complete
    when parts (1) to (4) of R1-SUBMISSION-MIN are. It goes to ICML 2027 (abstract 14 Jan, full paper 22 Jan 2027) if
    it is complete in time; otherwise the author chooses the venue then (TMLR takes submissions at any time).

## 5. Time, sharing and GPU-hours (R1-CARD-SHARE, R1-NO-TIMEOUT)

- A job may share a card with another process when its memory fits. Speed is not a result. An attempt lost to the
  card or the host is an infrastructure failure and is repeated; the author accepts that risk.
- No wall-clock limit decides a check or an outcome. The run budget of a proposal (T1: 3 × the slowest census record;
  T0: 600 s) stays part of the task, and it decides only on an attempt that had its card to itself.
- GPU-hour figures are reporting thresholds: expansion G.1b 40; G.5 425; P.4 phase 1 40 (the probe counts); D.3a's
  projection 140. Reaching one is reported to the author at once and does not stop the work unless a defect is found.

## 6. Next actions by owner

- **Compute** advances the Ada P.4 probe and D.3 HTCondor preflight in parallel, completes the G.1b and P11 checks,
  and finishes the assigned D.3 runner and audit units. For TOpAS, stage inputs explicitly and verify their hashes in the container.
- **Local** finishes the G.5 assembly and consumer paths with independent review, supplies the D.3 constants and
  verify-seed unit, and resumes the HPO references after the G1/G6 interfaces are ready.
- **Coordinator** publishes reviewed units and authorised notes after their checks, updates the live queue and
  routes any decision that changes the experimental design or launch scope.
- **Writer and design** keep the outcome readings and evidence in sync. Use the [claim-to-table sheet](../docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)
  to place the actual effects and intervals in the manuscript when released.

## 7. Author decisions

Use the [live decision list](https://github.com/dowlingwong/Agent_paper_B/blob/coord/coordinator/AUTHOR.md) for
open design choices, phase-specific signatures and test releases.
