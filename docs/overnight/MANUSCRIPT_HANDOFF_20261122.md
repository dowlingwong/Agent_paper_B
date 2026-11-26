# Manuscript hand-off, 22 November 2026

**AI-assisted (Claude, manuscript agent). Not an author decision, not a proof check, not evidence.** Branch `mac-manuscript-20261122`, created from `origin/main` at `3c3f822a`. Nothing was pushed. Only `papers/r1/` and this file were changed. No sealed label, evaluation value or result file was opened (`label_block.jsonl` and `evaluation_block.jsonl` in `reports/b2_audit_20261119/` were not read).

The text assumes the author's submission-version decision of 22 Nov as given to this agent (keep C1, C2, C3 as the offline ladder A0–A6 on T0 plus the T1 nodes labelled when the arms are frozen, under the frozen gate; the first brief said "at least three T1 nodes", which the coordinating session corrected on 22 Nov to the preregistered partial-T1 rule, and one small closed-loop check on T0; cut or move to the appendix T2, the API proposer, R-B, H2, the aggregation round and further T1 closed-loop runs; C4 as an assumption with offline checks). The PLAN rows for that decision are being recorded on another branch and were not available here.

## 1. What was written, per file

| File | State |
|---|---|
| `generated/numbers.tex` | Two blocks. (a) Committed facts as macros, each with its source file: sweep-1 audit counts (`reports/b2_audit_20261119/counts.json`), sweep-2 collection counts (`reports/sweep2_20261116/SWEEP2_REPORT_20261121.md`), gate power (`authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`), two constants of the 10(c) example (`proposals/T4_PROP10_REVISION_20261028.md` §4). (b) Placeholders defined as `\TBD{...}`, including `\Cell` for empty table cells and `\FigShell` for figure shells. |
| `sections/theory.tex` | Rewritten to revision 3 of the T4 revision. Main text: one-step index (Proposition 8′ parts 1–3 with the Gaussian closed form), selection bias of the record for any adaptive proposer (T4 Proposition 9 with the audit's added assumptions), reduction theorem under (NF) and (NI) (10(a′)), failure proposition (T4 10(b) as part (a), 10(c) as part (b)) with the 10(c) example. Scope paragraphs: fixed run price; the actual loop lies outside the theorem (author decision R1 option (ii)); what the reduction supports; relation to classical tools. Errata of R1-T4-PROOF-CHECK applied: 8′ needs no independence of U; μ = 0 edge case; identification of no-ops needs no mass at zero; Step 1 uses the tower property; the gap is the positive part of the difference; the existence statement is kept. The proof-check banner is kept and reworded to say what was and was not checked. |
| `sections/problem.tex` | Loop, observation model, information, objective. Three estimands (audited increment, offline one-step utility, closed-loop value) and the caveat that the offline utility is a proxy that relies on decision independence. C1 rates named. Precise DAC statement: parameters (screening threshold, keep threshold, verification count), instances (node, seed, manager, budget), learned forecaster with a derived rule (predict then optimise), reduction as a conditional theorem supported by synthetic controls, pilot ended before its evidence stage. |
| `sections/setup.tex` | Tiers T0 (eight nodes, seven primary, `openml_wdbc` sensitivity) and T1 (eight prepared nodes from three suites); noise level, qualification and liveness; two sweeps and proposers with committed counts; what differs between the sweeps; hosts by hardware class; audit protocol (population, K = 10, label and evaluation blocks, soft labels, sealing and staged release, splits); arm table A0–A6; the preregistered gate (run price, utility, oracle, IQM of gap closed, PoI, eligibility, floors, Holm, pass rule, one read); reported power; secondary analyses; closed-loop check. |
| `sections/method.tex` | Forecast (12 bins; π, μ, τ), rule and rule layer, forecasters A1–A6. A6 is "decision-focused fine-tuning", described as cost-sensitive classification on logged labels (TRACK_P §6.3, R1-BX-D9). Selection by development RPS skill (PRE-SELECT A). Cut arms referenced to Appendix B. |
| `sections/introduction.tex` | Problem, known problem with the two workshop papers and the gate family, four open questions, the four headline differences (a)–(d), DAC framing, contribution list with result claims as `\TBD`. C1 is stated as supporting evidence, not a first measurement. |
| `sections/related.tex` | Full draft: position paragraph with (a)–(d); measurements of noise; statistical gates; prediction before execution; decision-focused training and learned controllers; DAC; selection under noise; companion manuscript (placeholder kept). |
| `sections/results.tex` | Shell only, no numbers: C1 table per node, offline ladder table, leave-one-suite-out table, closed-loop table, sensitivity table (with and without `openml_wdbc`, full test population, two run prices), two figure shells, one-line reading guides, and two marked alternative openings (gate passes; gate does not pass). |
| `sections/limitations.tex` | Design limitations that follow from committed facts; result-dependent limitations `\TBD`. Not in the deliverable list; added for consistency with the new estimand caveat and the power statement. |
| `sections/appendix.tex` | A: "Deviations and post-hoc amendments" in four tables. B: components outside the submission version. C: further theory statements (T2 Propositions 1–5 and T4 Propositions 7, Corollary 8a, edge cases, shared-error model, summed gains, offline-evaluation bias, both failure examples with the closed-form table, the five offline checks). D: proofs of the three main statements. E: proposer exam disclosures. F–I: placeholders as before. |
| `refs/positioning_20261122.bib` | New entries: `jalaian2026noise`, `grover2026lucky`, `sgm2025`, `lonkar2026evidence`, `mlgym2025`, `mlagentbench`, `autoresearchloop`. Existing entries of `l6_bibliography_draft.bib` are reused for SAGE, PACE, Zhang et al., ARC, FOREAGENT, Beneath the Diff, "Visible but Not Avoided", Harness-MDP, the Ladder, Xie and Frazier, Chick and Frazier, Smith and Winkler, ifBO, LLAMBO. |
| `main.tex` | `array` package, the `L{}` column type, and the new bibliography file. Nothing else. |

`sections/abstract.tex` is unchanged (`\TBD`).

## 2. Deviations appendix: verification of each row

Every row was checked against its PLAN §10 row (or the named committed report) before it was listed. None of the items requested had to be omitted.

| Item | Rows checked |
|---|---|
| Stage A prompt set frozen post hoc | R1-EXAM-PROMPTSET-FREEZE, R1-EXAM-PROMPT-HISTORICAL-ANCHOR, R1-EXAM-PROMPT-FREEZE-1200 |
| Track X A1 template amendment | R1-EXAM-TEMPLATE-POLICY, R1-EXAM-TEMPLATE-AMENDMENT-PROPOSAL / -V16 / -IMPLEMENTED, R1-EXAM-STAGEA-ACCEPT. `gemma4_31b` is one of the four BOS-artifact candidates named in the proposal row; the table says so. |
| B1 anchor-gate change (R4) | R1-EXAM-B1-ANCHOR-R4, R1-EXAM-B1-ANCHOR-R4-H2 |
| Selection rule v1 → v2 (added) | R1-MAIN-PROPOSER (a), R1-EXAM-RULE-X5V2 |
| D28 liveness repair of four nodes | R1-D28-REPAIR; outcome (three re-qualified, the fourth replaced by the reserve) from `STATUS.md` ("Four repaired nodes measured …") and the T0 node list |
| Main proposer changed (added) | R1-MAIN-PROPOSER, R1-EXAM-X7 |
| `cache_prompt` and sweep 1 not seed-replayable | R1-SWEEP1-CACHE-DISCLOSURE, R1-CACHEPROMPT-FALSE |
| Sweep-1 run labels (added) | R1-SWEEP1-CLASSIFY |
| 7 of 8 nodes at the sweep-2 launch | R1-S2C3B-WDBC, `SWEEP2_REPORT_20261121.md` |
| Six admitted runtime-error records | R1-SWEEP2-RTE-DIAG, `SWEEP2_REPORT_20261121.md` |
| GPU model of sweep 2 (added) | R1-SWEEP-HOST-HTC, R1-SWEEP2-ANY-GPU, R1-SWEEP2-MEASURED-GPU |
| Host of the sweep-2 audit (added) | R1-SWEEP2-B2-DECISIONS, R1-SWEEP2-B2-GO |
| Host changes for the T1 table | R1-T1-HOREKA, R1-TRACKG-G1B-HOST, R1-T1-HOST-H200, R1-T1-HOST-TASL |
| Third suite replaced (added) | R1-1GC-FALLBACK |
| MLGym data manifests (added) | R1-T1-DATA-MANIFEST |
| K = 10 audits | R1-BX-D3, R1-BX-PROPOSED-CONFIRM (D3), R1-G5-DECISIONS; pilot seed use from R1-SWEEP1-CLASSIFY and C3_DESIGN §4 |
| Gate criterion (added) | R1-BX-D8, R1-BX-D8-V3-A, R1-BX-D8-V3-B, R1-BX-D8-CONFIRM, R1-BX-D8-CONFIRM-V31, R1-SWEEP2-PREREG |
| Earlier engineering reads of sweep-1 labels (added) | R1-TRACKP-SFT-DEV; preregistration PRE-SPLIT B and §4 step 4, §6 |
| Sequentiality pilot ended before its evidence stage | R1-TRACKS-FRAMING, R1-TRACKS-STOP4-END, R1-TRACKS-STOP4-CONSEQUENCES |
| Global-optimality statement replaced (added) | R1-T4-DI-FIX, R1-T4-PROOF-CHECK |
| Scope of the submission version (added) | no row on this branch; the row-id cell is `\TBD` |

**Host names inside record identifiers.** Two identifiers contain a host name. They are masked in the manuscript: `R1-T1-[cluster]` is R1-T1-HOREKA, and `R1-T1-HOST-[workstations]` is R1-T1-HOST-TASL. The decision log itself contains host names and the author's name; it needs anonymising before it can be part of the artifact (the appendix carries a `\TBD` for this).

## 3. Every `\TBD`, grouped by what it waits for

Counts are sites in `sections/*.tex` (41 explicit sites) plus uses of placeholder macros.

**A. Waits for results or data (15 sites, 14 macro uses, 99 table cells, 2 figure shells).**
- `introduction.tex`: the C3 claim (gate verdict, effect sizes, closed-loop check).
- `setup.tex`: T1 collection counts and per-node audit budget. Macros: `\TOneNodesUsed`, `\NoiseFloorTable`, `\SweepTwoAuditCounts`.
- `results.tex`: the shell banner; the two alternative-opening markers (one alternative is deleted after the gate read); "which effect sizes the data exclude"; T1 rows of the C1 table; the ladder paragraph; the leave-one-suite-out paragraph; the closed-loop paragraph; the sensitivity paragraph. Macros: `\GateVerdict`, `\GateIQM`, `\GatePoI`, `\GateEligibleNodes`, `\COneHeadline`, `\Cell` (99), `\FigShell` (2).
- `limitations.tex`: empirical limitations.
- `appendix.tex`: which T1 closed-loop runs finished; results of the five offline checks; the synthetic-control table (the existing T5 outputs are ENGINEERING_ONLY and are not cited).

**B. Waits for the author's proof check (6 sites).**
- `theory.tex` banner; `appendix.tex` banners of "Further theory statements" and "Proofs"; proofs of the appendix statements; `introduction.tex` and `limitations.tex` status lines.

**C. Waits for an author decision or approval (12 sites).**
- `abstract.tex`: the abstract.
- `problem.tex`: exact operational definitions of the four C1 rates (not found in a committed file).
- `method.tex`: whether the shared-representation and smoothed-rule variants (R-A2, R-A3) are reported.
- `setup.tex`: the reference rows beside the ladder (fixed-r replication with a t-test, A1-ctx, TabPFN, the base-model control); the design, matching and pre-declaration of the small closed-loop check.
- `results.tex`: layout of the C1 table (one panel per sweep, or pooled).
- `related.tex`: the anonymous companion reference.
- `appendix.tex`: the anonymised artifact and decision log; the row ids of the 22 Nov scope decision; the decision-model exam protocol and results; the AI-assistance disclosure; the workshop-overlap statement.

**D. Waits for facts to be filled from committed records (8 sites; no new evidence needed).**
- `method.tex`: adapter rank, learning-rate grid, selected checkpoint.
- `setup.tex`: screening funnel per suite; citation, exact identifier and quantisation of the main proposer.
- `appendix.tex`: update of the K row if a check row is published; citation of the arms-frozen record; exam protocol and stage tables; full premise table of the exam appendix report; compute and reproducibility.

`generated/numbers.tex` still defines the two skeleton placeholders `\ResultNoiseFloor` and `\ResultOfflineGate`; they are not used in the text.

## 4. Facts that could not be verified

**Bibliography (each has `note = {TO VERIFY ...}`).**
- `jalaian2026noise`: authors' given names.
- `grover2026lucky`: author's given name.
- `lonkar2026evidence`: author's given name.
- `sgm2025` (arXiv 2510.10232): authors and exact title; only the name "Statistical Gödel Machine" and the identifier were given.
- `mlgym2025` (arXiv 2502.14499, from PLAN §6): authors and exact title.
- `mlagentbench`: authors, title, venue, year (no identifier in a committed file).
- `autoresearchloop`: author, version, citation form (the bibliography draft deliberately excluded this software citation).
- The main proposer (`gemma4_31b`) has no citation; the text carries a `\TBD`.

**Numbers quoted about other papers.** The figures for Jalaian and Dasari and for Grover in `introduction.tex` and `related.tex` come from the coordinating session's verified list of 19–22 Nov 2026, reproduced in §5 below so that they trace to a committed file. They were not re-opened by this agent. The 28–63 % range for "Visible but Not Avoided" comes from `inputs/NOVELTY_FULLTEXT_20261019.md` §4.

**Other.**
- The task named "the 15 Nov errata on Propositions 8′ and 10(a′)". The row found is **R1-T4-PROOF-CHECK, dated 16 Nov 2026**; the 15 Nov rows are the Track S rows. The manuscript cites 16 Nov.
- T2 Propositions 2–5 in the appendix are written from the corrected restatements in `T_AUDIT_20261027.md`. The symbols (σ_t, σ_s, the fixed and vary split policies) were not re-derived against `T2_DERIVATIONS.md`.
- Part (a) of the failure proposition (T4 10(b)) has the AI audit's "correct as an existence example" only; the author's check covered 8′, 10(a′) and 10(c).
- "T1 × 6" in the power statement is read as six instances per T1 node (three test instances), from `reports/M11_D8_PASS_20261116.md`. "Effect size 0.3" is that simulation's g, not the run price.
- The sentence that an earlier pilot passed its gate spuriously with shared seeds comes from C3_DESIGN §4.
- `mlgym_houseprice` runs on CPUs although it belongs to the "GPU tier" T1; the text says "eight T1 nodes" without this detail.

## 5. Verified neighbour facts as received (for traceability)

Checked by the coordinating session on 19–22 Nov 2026; this agent used only these facts for these papers.

**Verification level (added by the coordinating session, 22 Nov):** these facts were read from conference listing pages and arXiv abstract pages through a summarising reader. No PDF was read. Every figure the manuscript quotes from these papers, and the description of how "Calibration Is Not Control" trains its model, must be checked against the PDF before submission (R1-C1-POSITION on branch `author-minsub-20261122`).
- Jalaian and Dasari, "Your Research Loop Is Measuring Noise: Accept Rules for Autonomous Experimentation", NeurIPS 2026 workshop "AI for Science: Verification in the Age of AI Scientists" (poster), https://neurips.cc/virtual/2026/156529. Replays accept rules on real runs (16 conditions each re-run 30 times; 1,280 logged hyperparameter trials). One run keeps 49.9 % of truly neutral candidates; peeking after every run gives 11.3 % false accepts at nominal 5 %; a Robbins normal-mixture e-process holds 5.3 %; a 20-run calibration phase holds the nominal level. No learned predictor, no cost-aware Bayes rule, no pre-execution screening.
- Grover, "Separating Real Improvements from Lucky Runs in Autonomous ML Research", NeurIPS 2026 Workshop for Autonomous Machine Learning Research (poster), https://neurips.cc/virtual/2026/157611. Controlled nanoGPT; 60 seeds; best-of-32 selection alone gives an apparent gain of 0.00544 val bpb, 2.7 times its preregistered threshold 0.002; frozen bank of 24 candidates over 749 runs: 9 exact nulls; of the other 15, 8 replicated, 3 failed, 4 inconclusive. Measurement and confirmation only.
- SAGE (arXiv 2609.36043): gate for self-evolving agents that edit a skill document; paired per-item comparison, one-sided exact binomial test on discordant pairs plus a regression cap; five benchmarks, four backbones; no learning; decides after evaluation.
- PACE (arXiv 2606.08106): anytime-valid paired commit gate (McNemar discordant pairs with a betting e-process); bounds each candidate's false-commit probability under optional stopping.
- SGM (arXiv 2510.10232): statistical tests with a global error budget for recursive self-modification.
- Lonkar (arXiv 2611.16378): frozen candidate, fresh audit samples, Hoeffding lower confidence bounds, non-inferiority on protected capabilities, canary deployment; synthetic Monte Carlo study only; no model of the value of acceptance or of run cost.
- Zhang et al. (arXiv 2606.21399): trains the supervision target on intervention utility instead of calibrated failure risk; ALFWorld.
- Taparia, Sagar and Senanayake (arXiv 2602.11574): RL policy that selects a per-query agent configuration (workflow, tools, budget).

## 6. Build and checks

- **Build.** TeX is present. `latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex` in `papers/r1/` (output directed to a scratch directory outside the worktree) exits 0 with no LaTeX warning, no undefined reference or citation and no overfull box. It was repeated from a `git archive` of the branch head. The root Makefile on this branch has no `paper` target, so `make paper` was not used.
- **Final build.** With `\FinalPaper` defined the build stops at the first `\TBD`, as intended.
- **Length.** The draft PDF has 25 pages; the main body ends on page 14. The 2026 style allows eight pages of main body, so the text needs cutting once the results are in (the setup section and the result shells are the largest parts).
- **Anonymity grep** over `main.tex`, `sections/`, `generated/`, `refs/positioning_20261122.bib` and `refs/anonymous.bib` for "Dowling", "Wong", "KIT", "ETP", "Karlsruhe", "TASL", "deepthought", "zhixu", "nemo", "horeka", GitHub URLs and Tailscale: no hit after masking the two record identifiers of §2. `refs/l6_bibliography_draft.bib` (not edited) has three GitHub URLs, all third-party (a DACBench comment, a calibration notebook entry, llama.cpp).
- **Terminology grep.** "reinforcement learning" appears three times, each for the cut optional arm (method "what is not part of the method", and Appendix A/B). "RL" does not appear. No em-dash.
- **Number scan.** Every numeral in `sections/` was listed by script and traced to a committed file or to §5.

## 7. Open questions for the author

1. **Proof-check banner.** PLAN row R1-T4-PROOF-CHECK records your check of 8′, 10(a′) and 10(c). The banner is kept as instructed and now says that the manuscript wording, the selection-bias proposition and the appendix statements are unchecked. Should the banner be narrowed further, or do you want to check the manuscript text first?
2. **C1 definitions.** The four rates are named, but no committed file fixes their operational definitions (for example how an audited increment within its standard error of zero is counted). They should be fixed before audit values are read.
3. **Closed-loop check.** Nodes, instances, repetitions, the matching report and a pre-declaration are open. The text states only arms A0–A3, matched budgets and the audited outcome.
4. **"H2".** The cut is read as C3_DESIGN's contrasts H2a and H2b (A5 minus A3). The gate itself still tests A3 and A5 against A2, as frozen. A6 is reported descriptively and is not a gate arm. Please confirm.
5. **Reference rows.** Which of fixed-r replication with a t-test (r = 3, Welch, α = 0.05 is still "proposed"), A1-ctx, TabPFN and the base-model control appear beside the ladder.
6. **Main proposer.** Exact model identifier, quantisation and citation.
7. **Decision log in the artifact.** The deviations tables cite PLAN row ids; the log needs anonymising (host names, author name) before release.
8. **Companion manuscript.** The placeholder citation and its sentence are unchanged.
9. **Title.** Unchanged. It still reads as a DAC headline; the text now states the reduction as a conditional theorem.
10. **Commit author.** Commits use the identity configured in this worktree (`Claude <noreply@anthropic.com>`), as instructed for this task; the Mac runbook asks for the author's identity on merged commits.
