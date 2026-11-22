# Paper B (route R1): the plan as it stands

**As of 22 Nov 2026 (after the rows of "22 November 2026 (d)"). AI-assisted (chat-session Claude). A view, not an authority: PLAN §10 rows control wherever they differ (R1-CURRENT-DOC). Dates are targets.**

## 1. What the paper claims

Noise-aware dynamic algorithm configuration (DAC) of a governed autoresearch loop (R1-ROUTE-DAC). Nothing is established yet.

| Claim | Content | Evidence it needs |
|---|---|---|
| C1 | Control errors of the default keep rule: false keeps, missed keeps, the winner's curse of the recorded incumbent, runs wasted on duplicate and inert edits. Positioned as supporting evidence, not a first measurement (R1-C1-POSITION). | Fresh-seed audits of sweep 1 and sweep 2 on T0 |
| C2 | Theory of acceptance and screening under noise for a ledger-dependent proposer. The main text carries only author-checked statements (R1-SUBMISSION-MIN). | Proof check; closed loop D.3a |
| C3 | A learned per-proposal forecast of the increment distribution, plugged into the C2 rule: ladder A0–A6 against the index policy (R1-C3, C3_DESIGN). | The preregistered offline gate; closed loop D.3b |
| C4 | In the submission: decision independence as a stated assumption with an offline check. The forced-branch test is in the follow-up paper (R1-SUBMISSION-CUTS). | Offline check on existing branch pairs |

Wording rules: the learned object is a forecaster and the policy is a derived rule applied to it; the reduction to one-step decisions is a conditional theorem; A6 is decision-focused fine-tuning; "RL" is not used (R1-BX-D9, R1-C1-POSITION).

## 2. Submission version (R1-SUBMISSION-MIN)

1. C1 from the two audited sweeps.
2. C2 with checked statements only.
3. C3 offline: one read of the preregistered gate on T0 and on the T1 nodes labelled by the cut-off.
4. Closed loop on T0 (D.3a rule arms, D.3b learned arms).

Cut from this version (R1-SUBMISSION-CUTS): tier T2, the API proposer, closed loop on T1, arm R-B, the aggregation round, the debiased-memory A/B, the information-matched TabPFN comparison, closed loop on non-qualifying nodes.

If the gate does not pass (its simulated power is 0.36 at effect size 0.3; 0.26 for T1 × 6), the paper reports effect sizes with intervals and claims C1, C2 and the ladder up to the rule arms.

## 3. Data and state

| Item | State on 22 Nov | Row |
|---|---|---|
| Proposers | Sweep 1: `qwen2.5-coder:7b`. Sweep 2 and everything after: `gemma4_31b`, thinking off (the Track X pick). | R1-MAIN-PROPOSER, `authorizations/c3_sweep2_20261119.md` |
| T0 (8 CPU nodes) | Sweep 1 audited (PASS, 19 Nov). Sweep 2 collected 21 Nov (288 campaigns, 5,760 trials); its fresh-seed audit started 22 Nov on deepthought. Primary T0 set: the seven nodes that passed liveness; `openml_wdbc` is a sensitivity row. | R1-SWEEP2-B2-GO, R1-S2C3B-WDBC, PRE-WDBC |
| T1 (GPU nodes) | Eight nodes: `mlab_cifar10`, `mlab_imdb`, `mlab_ogbn_arxiv`, `mlgym_cifar10`, `mlgym_fmnist`, `mlgym_breakout_minatar`, `mlgym_houseprice`, `autoresearch_fixedtokens`. Noise floors (G.1b) and the pilot (G.4) are running or signed on the TASL pair; the label runs (G.5) are under review: about 305 GPU-h at K = 10. | R1-T1-HOST-TASL, R1-G4-DECISIONS, R1-G5-DECISIONS |
| Labels | Train and dev blocks of sweep 1 and sweep 2 are released. Test and evaluation blocks stay sealed until the arms-frozen record. Audits: K = 10; label seeds 7001–7005, evaluation seeds 7006–7010. | R1-S2-LABELS-TRAINDEV-RELEASE, R1-SWEEP2-PREREG |
| Decision models (Track P) | P.4 phase 1 (SFT) decided; image v2.1 for HTCondor. A5 and A6 must be frozen before the gate read. | R1-TRACKP-P4-DECISIONS, R1-TRACKP-IMAGE-V21 |
| Gate | Preregistration frozen 21 Nov: gate v3.1, one primary read, split 1/3 : 1/6 : 1/2, pass rule b2. | R1-SWEEP2-PREREG, R1-BX-D8-CONFIRM-V31 |
| Theory | T2 and T4 revised; every statement awaits the author's proof check. | `theory/`, R1-SUBMISSION-MIN |
| Manuscript | Being drafted from 22 Nov on branch `mac-manuscript-20261122` (positioning, theory, setup, related work, deviations table, results skeleton for both outcomes). | R1-SUBMISSION-MIN |

## 4. Hosts

| Work | Host |
|---|---|
| T0 sweeps (proposer on GPU) | HTCondor, a GPU model with a measured chunk time (H200 so far) |
| T0 audits | deepthought CPUs |
| T1 table (noise floors, pilot, labels) | TASL-2 (worker) and TASL-7 (proposer server); one host pair for the table |
| Track P training | TASL cards or HTCondor image v2.1, one host per table |
| Closed loop D.3a/b | HTCondor GPU for the proposer, CPU workers; not the TASL pair (R1-D3-MIN) |

## 5. Dates

| Date | Milestone | Row |
|---|---|---|
| now | Manuscript drafting; D.3a pre-declaration and authorization note | R1-SUBMISSION-MIN, R1-D3-MIN |
| early to mid Dec | D.3a runs (rule arms, T0) | R1-D3-MIN |
| about 15 Dec (11 Dec at K = 6) | B.7: T1 labels and audits complete | R1-G5-DECISIONS |
| 20 Dec at the latest | Arms-frozen record; then test release and the single gate read | R1-ARMS-FREEZE-CUTOFF |
| 22 Dec to 3 Jan | D.3b (learned arms, T0); secondary analyses | R1-D3-MIN |
| 3 Jan | Last day for optional items to enter | R1-SUBMISSION-MIN |
| 10 Jan | Full draft; mock review until 13 Jan | R1-BX-D14 |
| 14 Jan / 22 Jan | Abstract registration / submission | ICML 2027 |

Slack: five days between B.7's target and the cut-off. If the T1 table slips further, the cut-off decides which T1 nodes are in the primary read; it does not move without an author row.

## 6. Process (R1-PROCESS-TIERS)

- Tier E (evidence runs, sealed or test partitions, preregistrations, notes, launch bindings, gate code): unchanged.
- Tier S (support code and documents): one fresh-session review and one correction round.
- Tier D (drafts, prompts, this file, dry runs): checked at merge, no separate review record.

## 7. Open for the author

1. **Proof check of the load-bearing statements** (one-step index, winner's curse, global-optimality conditions): who checks, and by when. Statements not checked by 3 Jan leave the main text.
2. **Order of the G.5 label runs** (proposal, not decided): run the seven cheaper nodes first and `autoresearch_fixedtokens` (about 138 of the 305 GPU-h) last, so that the cut-off can cost at most that one node and its suite's leave-one-suite-out fold.
3. **K = 6 on T1**: the K-check row (R1-BX-D3) would bring B.7 to about 11 Dec.
4. **D.3a**: its pre-declaration and authorization note (to be drafted).
5. **Co-authors and the ICML 2027 submission quota**: the quota page could not be opened on 22 Nov; check it before another ICML submission is planned.
6. **A dev-tuned static threshold arm**: confirm that the ladder has a static (screen, keep) pair tuned by search on dev campaigns, not only theory-derived constants; add it to D.3a if it is missing.
