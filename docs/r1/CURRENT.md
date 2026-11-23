# Paper B (route R1): the plan as it stands

**As of 22 Nov 2026 (after the rows of "22 November 2026 (d)"). AI-assisted (chat-session Claude). A view, not an authority: PLAN §10 rows control wherever they differ (R1-CURRENT-DOC). It introduces no decision. Dates marked "target" have no row.**

## 1. What the paper claims

Noise-aware dynamic algorithm configuration (DAC) of a governed autoresearch loop (R1-ROUTE-DAC). Nothing is established yet.

| Claim | Content | Evidence it needs |
|---|---|---|
| C1 | Control errors of the default keep rule: false keeps, missed keeps, the winner's curse of the recorded incumbent, runs wasted on duplicate and inert edits. Positioned as supporting evidence, not a first measurement (R1-C1-POSITION). | Fresh-seed audits of sweep 1 and sweep 2 on T0 |
| C2 | Theory of acceptance and screening under noise for a ledger-dependent proposer. The main text carries only author-checked statements: today T4 Propositions 8′, 10(a′) and 10(c) (R1-T4-PROOF-CHECK, R1-SUBMISSION-MIN). | Proof check of the remaining statements; closed loop D.3a |
| C3 | A learned per-proposal forecast of the increment distribution, plugged into the C2 rule: ladder A0–A6 against the index policy (R1-C3, C3_DESIGN). | The preregistered offline gate; closed loop D.3b if the gate passes |
| C4 | In the submission: decision independence as a stated assumption with an offline check. The forced-branch test stays deferred (R1-T4-PROOF-CHECK, R1-SUBMISSION-CUTS). | The offline checks of T4 §6 |

Wording rules: the learned object is a forecaster and the policy is a derived rule applied to it; the reduction to one-step decisions is a conditional theorem; A6 is decision-focused fine-tuning; the term "RL" is not used (R1-BX-D9, R1-C1-POSITION).

## 2. Submission version (R1-SUBMISSION-MIN)

1. C1 from the two audited sweeps.
2. C2 with checked statements only.
3. C3 offline: one read of the preregistered gate on T0 and on the T1 node set of the arms-frozen record.
4. Closed loop on T0: D.3a rule arms, six with the Ladder margin rule tuned on the dev label block (R1-MINSUB-CHOICES (4)); D.3b learned arms, only if the gate passes (R1-D3-MIN).

Cut from this version (R1-SUBMISSION-CUTS): tier T2, the API proposer, closed loop on T1, arm R-B, the aggregation round, the debiased-memory A/B, the information-matched TabPFN comparison, closed loop on non-qualifying nodes. Not run in closed loop (R1-D3-MIN): the racing-style rule, harness heuristics, random at matched budget, the AWR-MLP controller and the reference arms of R1-C3 (ladder). PLAN §9 items 2, 4, 5 and 6 are reduced accordingly (R1-SUBMISSION-MIN).

If the gate does not pass (simulated mean two-arm power 0.36 at effect size 0.3; 0.26 for T1 × 6; qualifiers as in R1-BX-D8-V3-B), RUNBOOK B.7 and §6 apply: C3 is reported as the measured negative, with effect sizes and intervals, and C1, C2 and the D.3a result carry the paper.

## 3. Data and state

| Item | State on 22 Nov | Row |
|---|---|---|
| Proposers | Sweep 1: `qwen2.5-coder:7b`. Sweep 2 and everything after: `gemma4_31b`, thinking off (the Track X pick). | R1-MAIN-PROPOSER, `authorizations/c3_sweep2_20261119.md` |
| T0 (8 CPU nodes) | Sweep 1 audited (PASS, 19 Nov). Sweep 2 collected 21 Nov (288 campaigns, 5,760 trials); its fresh-seed audit is authorized on deepthought (R1-SWEEP2-B2-GO); no completion record is on `main` yet. Primary T0 set: the seven nodes that passed liveness; `openml_wdbc` is a sensitivity row. | R1-SWEEP2-B2-GO, R1-S2C3B-WDBC, PRE-WDBC |
| T1 (GPU nodes) | Eight nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`, `mlgym_houseprice`, `autoresearch_fixedtokens`. Noise floors (G.1b) and the pilot (G.4) are decided for the TASL pair; the label runs (G.5) have a draft note under review that still needs the author's signature: about 305 GPU-h at K = 10. | R1-T1-HOST-TASL, R1-G4-DECISIONS, R1-G5-DECISIONS |
| Labels | Sweep 1's train and dev blocks can be released. Sweep 2's release waits for its registered audit (R1-SWEEP2-RELEASE-DECISIONS). Test and evaluation blocks stay sealed until the arms-frozen record. Audits: K = 10; label seeds 7001–7005, evaluation seeds 7006–7010. | R1-SWEEP2-RELEASE-DECISIONS, R1-SWEEP2-PREREG |
| Decision models (Track P) | P.4 phase 1 (SFT) decided; image v2.1 for HTCondor. A5 is frozen in the arms-frozen record before the gate read; A6 is trained only after the gate passes (RUNBOOK P.5). | R1-TRACKP-P4-DECISIONS, R1-TRACKP-IMAGE-V21 |
| Gate | Preregistration frozen 21 Nov: gate v3.1, one primary read, split 1/3 : 1/6 : 1/2, pass rule b2. | R1-SWEEP2-PREREG, R1-BX-D8-CONFIRM-V31 |
| Theory | T2 and T4 revised. Author-checked: T4 Propositions 8′, 10(a′), 10(c), with errata. Not checked: the T2 propositions, T4 Propositions 6, 7, 9 and 10(b). | R1-T4-PROOF-CHECK, R1-SUBMISSION-MIN |
| Manuscript | A first draft exists on branch `mac-manuscript-20261122` (pushed with this branch, not merged): positioning, theory, setup, related work, deviations table, results shells for both outcomes. R1-BX-D14 planned writing from early December; starting earlier has no row. | R1-BX-D14 |

## 4. Hosts

| Work | Host |
|---|---|
| T0 sweeps (proposer on GPU) | HTCondor, a GPU model with a measured chunk time (R1-SWEEP-HOST-HTC, R1-SWEEP2-MEASURED-GPU) |
| T0 audits | Sweep 1 and sweep 2: deepthought CPUs, each by its own row (sweep 2: R1-SWEEP2-B2-GO, for that audit only). The D.3 audit: deepthought CPUs (R1-MINSUB-CHOICES (4)). |
| T1 table (noise floors, pilot, labels) | TASL-2 (worker) and TASL-7 (proposer server); one host pair for the table (R1-T1-HOST-TASL) |
| Track P training | As R1-TRACKP-P4-DECISIONS and R1-TRACKP-IMAGE-V21 state |
| Closed loop D.3a/b | HTCondor GPU for the proposer, CPU workers; not the TASL pair (R1-D3-MIN) |

## 5. Dates

| Date | Milestone | Row |
|---|---|---|
| after the sweep-2 train/dev release | D.3 pre-declaration (both stages) and D.3a note; then D.3a runs (target: December) | R1-D3-MIN |
| about 12 Dec | T1 labels complete at K = 10 (target; about 8 Dec at K = 6) | R1-G5-DECISIONS and its date model |
| about 15 Dec | Gate read, B.7 (target; about 11 Dec at K = 6) | R1-G5-DECISIONS |
| 17 Dec at the latest | T1 train/dev release row (planning value, until arm training time is measured) | R1-ARMS-FREEZE-CUTOFF |
| 20 Dec at the latest | Arms-frozen record; the gate read follows it | R1-ARMS-FREEZE-CUTOFF |
| gate read to 3 Jan | D.3b if the gate passes; secondary analyses (target) | R1-D3-MIN |
| 3 Jan | Last day for optional items and for further proof checks to enter | R1-SUBMISSION-MIN |
| 10 Jan | Full draft; mock review after it (target) | R1-BX-D14 |
| 14 Jan / 22 Jan | Abstract / full paper, ICML 2027, anywhere on earth (official page read 22 Nov) | R1-MINSUB-CHOICES (2) |
| 23 Feb / 3 May | First-stage rejection notices / final decisions | R1-MINSUB-CHOICES (2) |

If the T1 table holds its targets, the cut-off is not reached. If it slips, the cut-off decides the T1 node set of the single gate read; a suite without a labelled node then STOPs the leave-one-suite-out analysis (R1-ARMS-FREEZE-CUTOFF (d)).

## 6. Process (R1-PROCESS-TIERS)

- Tier E (evidence runs; sealed or test partitions; preregistrations, pre-declarations, notes and their drafts; launch bindings; gate, fold, label-writing, audit and arm-training code; the arms-frozen record; D.3 analysis scripts): unchanged procedure.
- Tier S (other support code and documents): one fresh-session review committed under `reviews/`, and one correction round.
- Tier D (manuscript text, other proposals, this file, dry runs): checked at merge, no separate review record.

## 7. Open for the author

1. **Theory statements** (R1-PROOF-POLICY): an independent AI proof check plus the coordinating chat's spot check decide entry to the main text; the author's own check is no longer required. The AI check of T2 Prop. 1, T4 Props. 6, 7, 9 (restated) and 10(b) is running.
2. **ICML submission form** (before 14 Jan): the author list, the eligible reciprocal reviewer (or the exemption, which limits each author to one such submission), and the contribution type.
3. **G.5 note**: it still needs the author's signature, with the run order of R1-MINSUB-CHOICES (1) written in (one cheap node per other suite, then `autoresearch_fixedtokens`, then the rest).
4. **K = 6 on T1**: the K-check's cost is to be reported; K = 6 needs its own row.
5. **D.3**: the pre-declaration is to be drafted by the coordinating chat (R1-MINSUB-CHOICES (4)), including a proposed LLM-call cap; it and the two authorization notes need the author's signature.
7. **Threshold correction** (R1-D3-CHOICES (1)): a direct ancestor–descendant test decides whether D.3a gains a seventh arm; D.3 signing waits for it. §13 of the D.3 draft is otherwise settled; the D.3b sidecar image stays open.
6. **Direct screening measurement** (R1-SCREEN-MEASURE): its pre-declaration and note are being drafted; the author signs before it runs on deepthought. The E1 runs of 22 Oct are accepted (R1-E1-PILOT-ACCEPT).

The recommendations behind this section's rows are in `proposals/MINSUB_RECOMMENDATIONS_20261122.md`.
