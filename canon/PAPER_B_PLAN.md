# Paper B (route R1): the plan as it stands

**As of 26 Nov 2026, `main` after the rows of "26 November 2026 (f)". AI-assisted (coordinating chat, Claude).**
A view, not an authority: `docs/r1/PLAN.md` §10 rows control wherever they differ (R1-CANON-FOLDER). It introduces no
decision. Dates marked "target" are not gates (R1-BX-D14-G4B). Nothing is established yet: the gate is unread, no arm
is frozen, no closed-loop campaign has run.

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
| T1 | Eight GPU nodes from MLAgentBench, MLGym and autoresearch, code-level diffs, 12 instances per node; all enter C3 (D21 is recorded, not a filter). Up to four more nodes if their G.1b passes by 2 Dec | R1-T1-D21-SCOPE, R1-T1-NODE-EXPANSION, R1-G5-EXPANSION-JOIN |
| Arms | A0 default; A1 index policy; A2 A1 + rule layer; A3 tabular forecaster; A4 LLM self-assessment; A5 fine-tuned small LM; A6 after the gate only | R1-C3 (ladder), R1-ARMS-DECISIONS |
| Offline gate | A3 and A5 against A2: IQM of gap closed and probability of improvement, Holm; split 1/3 : 1/6 : 1/2; price 0.1 σ_node; simulated power 0.36 at effect 0.3 (0.26 for T1 × 6) | R1-BX-D8-V3-A/B, R1-BX-D8-CONFIRM-V31 |
| D.3a | T0, seven nodes × 18 new instances, W = 20, 80 LLM calls; arms A0, A0R, A1, A2, FIXR3, EGATE, LADDER; Y = audited final-vs-start gain / σ_node, K = 10 | R1-D3-MIN, R1-MINSUB-CHOICES (4), R1-D3-DECOMP |
| D.3b | A3, A5 as frozen, on D.3a's instances; contrasts against A2, A0 and A5 − A3; not conditional on the gate | R1-D3B-UNCONDITIONAL |
| D.3c | T1 pilot nodes `mlab_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`; A0, A2, A3, A5; descriptive | R1-D3-ORDER |
| Secondary outcomes | Budget curve Y(w), compute per campaign, runs-to-match, mechanism counts, offline–online agreement, learning by tier | R1-D3-OUTCOMES2 |
| Reference rows | Random search with de-duplication and SMAC3 as the proposer on T0 | R1-D3-HPO-REF |

Cut from the submission (R1-SUBMISSION-CUTS): tier T2, the API proposer, arm R-B, the aggregation round, the
debiased-memory A/B, the information-matched TabPFN comparison. Optional work enters only if reviewed by 3 Jan 2027.

## 3. State by track

| Track | State | Next |
|---|---|---|
| T0 labels | Both sweeps audited; label tables frozen; train/dev released (sweep 2: 850/422; sweep 1: 593/276); A3's T0 run reviewed | — |
| T1 noise floors | G.1b sealed for all eight nodes; cross-host checks xc2 and xc3 PASS (seven nodes may audit on TASL-7) | — |
| T1 pilot | G.4b PASS: 126 of 180 proposals ran (0.70); liveness 0.62 to 0.82 per node | — |
| T1 labels (G.5) | Code and draft note revision 13 on `main`; 216.9 GPU-h projected of 425; pilot-basis PASS on TASL-2; houseprice's CPU-set check STOPped on a procedure defect (it blocks that node only) | The fix (local worker); the author signs the note (S1–S14) |
| Expansion nodes | Titanic, ETTh1, MetaMaze, Forest Cover: kits and census PASS; G.1b spec on `main` (launch commit `7d0279d8`); four host checks and two determinism checks PASS, reviewed | Kit c1 disposition record (P2), note published, runs; cutoff 2 Dec 00:00 CET |
| Decision models (P.4) | Runner, probe mode, charging on `main`; host-config fill on a branch; the pool has had no batch GPU since 24 Nov | A direct-launch path for a host that fits (Ada first, R1-HOST-FREE), probe, author signs the revised phase-1 note |
| Gate | Preregistered 21 Nov, amended 23 Nov; unread | Arms-frozen record, then one read |
| Closed loop D.3 | Pre-declaration draft revision 3 (unsigned, branch `mac-d3-predecl-20261122`); runner, audit, table and three arms not built | R1-D3-ORDER |
| Theory | Main-text statements limited to those passing R1-PROOF-POLICY | The remaining checks before the gate read; the theory section is shortened in the restructure |
| Manuscript | `papers/r1`, about 22k words, both gate outcomes written | Restructure after R1-ALIGN-OUTCOME: question first, decomposition as the main table, procedure to the appendix |

## 4. Dates

| Date | Milestone | Row |
|---|---|---|
| 2 Dec 00:00 CET | Expansion G.1b cutoff | R1-T1-NODE-EXPANSION |
| ≈ 14 Dec (target) | Gate read B.7 | R1-BX-D14-G4B |
| 17 Dec at the latest | T1 train/dev release | R1-ARMS-FREEZE-CUTOFF |
| 20 Dec at the latest | Arms-frozen record | R1-ARMS-FREEZE-CUTOFF |
| 3 Jan 2027 | Optional work must be reviewed | R1-SUBMISSION-MIN |
| ≈ 9 Jan (target) | D.3 complete | R1-BX-D14-G4B |
| 14 Jan / 22 Jan | ICML 2027 abstract / full paper (anywhere on earth) | R1-MINSUB-CHOICES (2) |

## 5. GPU-hour caps in force

G.1b 100 (xc3's 2.0 inside it); expansion G.1b 40; G.5 425; P.4 phase 1 40 (the probe counts); D.3a projection STOP
at 140. Each is fixed by its note or row; an agent never raises one.

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
- Publish the expansion note; prepare the G.5 signing sheet; merge reviewed units; recompute dates when the expansion
  set is known.

**Writer and designer**
- Restructure the manuscript after R1-ALIGN-OUTCOME; the Paper C manuscript skeleton after the consolidation.

From R1-AUTONOMY on, the live queue is the task files on branch `coord/coordinator`; this section is the snapshot of
26 Nov.

## 7. Waiting on the author

- G.5 note: S1 to S14 (the pilot-basis PASS is on `main`); S9.
- Signatures: screening-measurement note; D.3 pre-declaration; P.4 phase-1 note (after the probe).
- Outside the repository: confirm who may use TASL-7's GPU. When the pool's GPUs return matters less now that work
  may move to Ada (R1-HOST-FREE).
