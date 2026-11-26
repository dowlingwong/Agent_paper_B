# Paper B (route R1): the plan as it stands

**As of 26 Nov 2026, `main` after the rows of "26 November 2026 (g)". AI-assisted (coordinating chat, Claude).**
A view, not an authority: `docs/r1/PLAN.md` §10 rows control wherever they differ (R1-CANON-FOLDER). It introduces no
decision. No calendar date and no wall-clock limit decides anything (R1-STEP-ORDER, R1-NO-TIMEOUT). Nothing is
established yet: the gate is unread, no arm is frozen, no closed-loop campaign has run.

## 1. Question and claims (R1-ALIGN-OUTCOME)

**Question.** At a matched worker-run budget and LLM-call cap, which control decisions of a governed autoresearch loop
raise the fresh-seed audited gain of a campaign, and by how much?

| Claim | Content | Evidence |
|---|---|---|
| Loop (headline) | Rule and learned control against the default loop at matched budget; what de-duplication, noise-aware decisions and a learned forecast each buy | Closed loop D.3 on T0: D.3a rule arms, D.3b learned arms (always run), D.3c on three T1 nodes (descriptive) |
| C3 offline | A learned per-proposal forecast improves one-step decisions on logged proposals against A2 | The preregistered gate, read once (R1-SWEEP2-PREREG, gate v3.1) |
| C1 | Control errors of the default keep rule: false keeps, missed keeps, the winner's curse, wasted runs. Supporting, not a first measurement (R1-C1-POSITION) | Fresh-seed audits of sweeps 1 and 2 |
| C2 | The one-step rule under noise for a ledger-dependent proposer, and the conditions under which it is globally optimal | Main-text statements pass the independent proof check and the coordinator's spot check (R1-PROOF-POLICY) |

Both confirmatory families (the gate; D.3's contrasts) are reported whatever they show. The declared reading of every
outcome combination is §6 of `docs/r1/proposals/GOAL_METRIC_ALIGNMENT_PROPOSAL_20261126.md`. No multi-step claim is
made; that is Paper C. Wording rules: the learned object is a forecaster, the policy is a derived rule, the term "RL"
is not used (R1-BX-D9).

## 2. Design

| Part | Content | Rows |
|---|---|---|
| T0 | Eight CPU nodes, single-parameter edits; seven in the primary set, `openml_wdbc` a sensitivity row. Two sweeps (7B manager; `gemma4_31b` thinking off), 18 instances per node, W = 20 | R1-MAIN-PROPOSER, PRE-WDBC |
| T1 | Eight GPU nodes from MLAgentBench, MLGym and autoresearch, code-level diffs, 12 instances per node; all enter C3 (D21 is recorded, not a filter). Up to four more nodes: each joins when its G.1b passes determinism | R1-T1-D21-SCOPE, R1-T1-NODE-EXPANSION, R1-G5-EXPANSION-JOIN, R1-STEP-ORDER |
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
| T1 labels (G.5) | Code and draft note revision 13 on `main`; 216.9 GPU-h projected of 425; pilot-basis PASS on TASL-2; houseprice's CPU-set check STOPped on a procedure defect (it blocks that node only) | The fix (local worker); the author signs the note (S1–S14) |
| Expansion nodes | Titanic, ETTh1, MetaMaze, Forest Cover: kits and census PASS; G.1b spec on `main` (launch commit `7d0279d8`); four host checks and two determinism checks PASS, reviewed | Kit c1 disposition record (P2), note published, runs; each node that passes joins G.5 by addendum |
| Decision models (P.4) | Runner, probe mode, charging on `main`; host-config fill on a branch; the pool has had no batch GPU since 24 Nov | A direct-launch path for a host that fits (Ada first, R1-HOST-FREE), probe, author signs the revised phase-1 note |
| Gate | Preregistered 21 Nov, amended 23 Nov; unread | Arms-frozen record, then one read |
| Closed loop D.3 | Pre-declaration draft revision 3 (unsigned, branch `mac-d3-predecl-20261122`); runner, audit, table and three arms not built | R1-D3-ORDER |
| Theory | Main-text statements limited to those passing R1-PROOF-POLICY | The remaining checks before the gate read; the theory section is shortened in the restructure |
| Manuscript | `papers/r1`, about 22k words, both gate outcomes written | Restructure after R1-ALIGN-OUTCOME: question first, decomposition as the main table, procedure to the appendix |

## 4. Order of steps (R1-STEP-ORDER)

No calendar date decides anything. A step starts when the steps it depends on are complete and reviewed; no step is
cut, shortened or reordered to meet a date.

**To the gate**
1. Expansion G.1b: kit c1 record, note published, the four nodes run. A node with determinism PASS joins the T1 set.
2. G.5: the author signs the note; label runs on the eight nodes; each passing expansion node joins by addendum.
3. Decision models (P.4): a launch path on a host that fits, the probe, the author signs the phase-1 note, training.
4. G.5 labels complete for every node of the set; then the T1 train/dev release row (author).
5. Arms trained, selected and calibrated; the arms-frozen record; the one gate read (B.7).

**To the closed loop** (beside 1 to 5)
6. Screening measurement: fix, smoke, the author signs, run.
7. D.3 pre-declaration revision 4, reviewed; the author signs.
8. Units G1, G3 to G8 and A0R, each reviewed; the per-arm smoke.
9. D.3a (does not wait for the gate); D.3b after the arms-frozen record; D.3c after the G.5 labels (optional).

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

## 6. Next actions by owner (26 Nov)

**Compute agent** (every server; R1-AGENT-COMPUTE)
1. Kit c1 disposition record for the four kits (P2 of the expansion note); then the four runs from `7d0279d8` once
   the note is published.
2. Survey of free resources on every host, and Ada's readiness for decision-model training, LLM serving and T1
   audits (R1-HOST-FREE).
3. G.5 on the TASL pair after its note is signed; houseprice's CPU-set check after the local worker's fix.
4. D.3: the screening measurement (after its fix and the author's signature); the campaign runner G1 and the Y audit
   G6 with the Y(w) points, each reviewed, with a launcher that does not depend on HTCondor.
5. P.4: the probe and the SFT runs on the first host that fits, once the direct-launch path and the note exist.
6. The torch test files of the host-config fill; who holds TASL-7's GPU.

**Local worker** (Mac)
0. The fix that makes the three sealed attempts of houseprice's CPU-set check producible.
0a. The rows of 26 Nov (g) in the notes and specs not yet signed or launched: no time bound in a check, no deadline,
   the shared-card repeat rule, GPU-hour figures as thresholds; reviewed values are kept (R1-NO-TIMEOUT (2)).
0b. R1-HOST-FREE units: a direct-launch path and host configuration for P.4 on a host outside HTCondor; audit hosts
   for G.5 beyond the TASL pair, each gated by a per-node cross-host PASS, through an addendum note; a launcher for
   D.3 that does not depend on HTCondor.
1. D.3 pre-declaration revision 4 (the rows of 26 Nov (d)), with `d3_analysis.py`; `mac-screen-measure-20261123`
   brought onto `main`.
2. Decision sheet S9: how an expansion node joins the frozen eight-node split.
3. D.3 units: A0R, FIXR3, EGATE, LADDER, run accounting, the outcome table, the A5 sidecar path and image.
4. The G.5 addendum mechanism; the two test-only fixes; the HPO reference unit; the D.3c scoping memo.
5. Paper C: one consolidated branch on current `main` (lowest priority).

**Coordinator**
- Publish the expansion note; prepare the G.5 signing sheet; merge reviewed units; report which steps are complete.

**Writer and designer**
- Restructure the manuscript after R1-ALIGN-OUTCOME; the Paper C manuscript skeleton after the consolidation.

From R1-AUTONOMY on, the live queue is the task files on branch `coord/coordinator`; this section is the snapshot of
26 Nov.

## 7. Waiting on the author

- G.5 note: S1 to S14 (the pilot-basis PASS is on `main`); S9.
- Signatures: screening-measurement note; D.3 pre-declaration; P.4 phase-1 note (after the probe).
- Nothing outside the repository blocks: work may move to Ada (R1-HOST-FREE) and may share a card (R1-CARD-SHARE).
