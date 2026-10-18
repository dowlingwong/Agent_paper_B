# Paper B novelty sweep, part 2: ranking & selection, KG, racing, BAI, noisy optimisation, decision-focused learning (2026-10-18)

*AI-assisted: run by an AI research subagent (Claude) on 2026-10-18 with WebSearch/WebFetch, at the author's request; recorded verbatim in substance by the coordinating session. Abstract-level verification unless stated. No human review. Part 1: `NOVELTY_SWEEP_20261009.md` (not repeated here).*

**Access failures.** HAL hal-00654404 / hal-00658212 and Bielefeld PUB (bot protection; verified via COLT PDF, BORIS Bern, le.ac.uk copies); projecteuclid (Bechhofer 1954); arXiv 2610.15738 (HTTP 429, not retried); INFORMS pubsonline abstracts (used IDEAS/RePEc).

## 1. Ranking & selection
| Work | Verified | What it does | Assumes (violated by the loop) / covers | Overlap |
|---|---|---|---|---|
| Kim & Nelson 2001, TOMACS 11(3) | https://www.cs.utexas.edu/~shivaram/readings/b2hd-KimNelson2001.html (bibliographic only) | KN fully sequential IZ selection | Fixed set, free resampling, no restore | L |
| Chen, Lin, Yücesan et al. 2000, DEDS 10 (OCBA) | https://www.doi.org/10.1023/A:1008349927281 | Replication allocation over a fixed design set | Budget only for sampling, never new proposals | L |
| Chick & Inoue 2001, Oper. Res. 49(5) | https://ideas.repec.org/a/inm/oropre/v49y2001i5p732-743.html | Bayesian EVI procedures, opportunity cost, unequal sampling costs | Fixed alternatives; covers cost-weighted VoI | M (C2-ii/v) |
| Nelson & Goldsman 2001, Mgmt Sci 47(3) | https://ideas.repec.org/a/inm/ormnsc/v47y2001i3p449-463.html | Comparisons with a standard; CRN can hurt | Standard is fixed, not a noisy recorded max | M |
| Kim 2005, TOMACS 15(2) | https://doi.org/10.1145/1060576.1060579 | Fully sequential comparison with a standard (known/unknown mean) | Covers "protect the incumbent" | M |
| Xie & Frazier 2013, Oper. Res. 61(5) | https://ideas.repec.org/a/inm/oropre/v61y2013i5p1174-1189.html | Bayes-optimal DP for multiple comparisons with a known standard under sampling cost | Known threshold; fixed set | **H** (C2-i/v maths) |
| Chick & Frazier 2012, Mgmt Sci 58(3) | https://ideas.repec.org/a/inm/ormnsc/v58y2012i3p550-569.html | Optimal sequential sampling, one uncertain alternative vs known standard, with sampling cost; DP beats one-step | Price per sample of an existing alternative; no proposer | **H** (C2-ii/v) |
| Branke, Chick & Schmidt 2007, Mgmt Sci 53(12) | https://ideas.repec.org/a/inm/ormnsc/v53y2007i12p1916-1932.html | Empirical comparison of IZ/OCBA/Bayesian procedures | i.i.d. normal, fixed set | L |
| Hong & Nelson 2007, IIE Trans. 39(7) | https://scholars.cityu.edu.hk/en/publications/selecting-the-best-system-when-systems-are-revealed-sequentially/ | R&S when systems are revealed sequentially | Generation independent of noisy outcomes; resampling allowed | **M–H** |
| Bechhofer 1954 | listing only | Origin of IZ | — | L |

## 2. Knowledge gradient and noisy-BO incumbents
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| Frazier, Powell & Dayanik 2009, INFORMS JoC 21(4) | https://collaborate.princeton.edu/en/publications/the-knowledge-gradient-policy-for-correlated-normal-beliefs/ | KG with correlated beliefs | Fixed set; correlation specified, not learned from content | M |
| Ryzhov, Powell & Frazier 2012, Oper. Res. 60(1) | https://ideas.repec.org//a/inm/oropre/v60y2012i1p180-195.html | Online KG, correlated priors | Fixed arm set | L–M |
| Letham et al. 2019, Bayesian Analysis (arXiv 1706.07094) | https://arxiv.org/abs/1706.07094 | Noisy EI | GP over parametric space | M (C2-iv) |
| Picheny, Wagner & Ginsbourger 2013, SMO 48(3) | https://boris.unibe.ch/41521 | Benchmark of noisy kriging infill criteria | GP | M |
| Zhou, Ma & Blaschko 2024, ACML (PMLR 222) | https://proceedings.mlr.press/v222/zhou24a.html | Corrected EI accounting for incumbent uncertainty | GP | **M–H** (C2-iv) |
| Wang, Wang, Ng & Petra 2025, arXiv 2508.15674 | https://arxiv.org/abs/2508.15674v1 | Noisy GP-EI regret under three incumbent choices incl. best observation | GP; no proposer, no keep/discard | **M–H** (C2-iv) |

## 3. Racing and intensification
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| Maron & Moore 1993, NIPS 6 | https://proceedings.neurips.cc/paper/1993/hash/02a32ad2669e6fe298e607fe7cc0e1a0-Abstract.html | Hoeffding races | Fixed set, cheap resampling | L |
| Birattari et al. c. 2002 (F-Race) | https://cs.ubc.ca/labs/algorithms/Courses/CPSC536H-10/Materials/BirEtAl02.pdf | Friedman-test racing blocked by instance | Fixed pool | L–M |
| López-Ibáñez et al. 2016, ORP 3 (irace) | https://research.manchester.ac.uk/en/publications/the-irace-package-iterated-racing-for-automatic-algorithm-configu/ | Iterated, elitist racing | Elites re-evaluated (opposite of frozen record) | M |
| Hutter et al. 2009, JAIR 36 (ParamILS) | https://www.jair.org/index.php/jair/article/view/10628 | Local-search configuration, adaptive capping | Incumbent on growing instance sets | L–M |
| Hutter, Hoos & Leyton-Brown 2011 (SMAC, TR-2010-10) | https://www.cs.ubc.ca/tr/2010/tr-2010-10 | Model-based configuration with intensification | Incumbent re-run when challenged | M (baseline) |
| Lindauer et al. 2022, JMLR 23(54) (SMAC3) | https://jmlr.org/papers/v23/21-0888.html | Maintained package | — | baseline |

## 4. Best-arm identification, infinite arms, thresholding
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| Audibert, Bubeck & Munos 2010, COLT | https://www.learningtheory.org/colt2010/papers/59Audibert.pdf | Fixed-budget BAI | Fixed K arms | L |
| Kaufmann, Cappé & Garivier 2016 (arXiv 1407.4443) | https://arxiv.org/abs/1407.4443 | Complexity of m-best identification | Fixed arms | L |
| Garivier & Kaufmann 2016, COLT (PMLR 49) | https://proceedings.mlr.press/v49/garivier16a.html | Track-and-Stop | Fixed arms | L |
| Carpentier & Valko 2015, ICML (PMLR 37) | https://proceedings.mlr.press/v37/carpentier15.html | Simple regret, infinitely many arms | i.i.d. reservoir; resampling | **M** |
| Aziz et al. 2018, ALT (PMLR 83) | https://proceedings.mlr.press/v83/aziz18a.html | Fixed-confidence pure exploration from a reservoir | i.i.d. reservoir | M |
| Locatelli, Gutzeit & Carpentier 2016, ICML (PMLR 48) | https://proceedings.mlr.press/v48/locatelli16.html | Thresholding bandit (APT) | Known fixed threshold | M |
| Kano et al., arXiv 1710.06360 | https://arxiv.org/abs/1710.06360v2 | Good-arm identification | Known threshold | M |

## 5. Noisy optimisation / evolutionary computation
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| Droste 2004, GECCO (LNCS 3102) | https://www.cs.york.ac.uk/rts/docs/GECCO_2004/Conference%20proceedings/bibs/3102/31021088.htm | (1+1) EA on noisy OneMax | Fixed mutation operator | M |
| Jin & Branke 2005, IEEE TEC 9(3) | https://www.cs.le.ac.uk/people/sy11/ECiDUE/JinBranke-TEVC05.pdf | Survey: averaging, sampling, threshold selection | Threshold acceptance under noise is an existing heuristic | M (C2-i) |
| Qian et al. 2016, Evol. Comput. | https://research.birmingham.ac.uk/en/publications/on-the-effectiveness-of-sampling-for-evolutionary-optimization-in/ | Value of resampling vs threshold selection | Fixed operators | M |
| Qian et al., arXiv 1810.05045 | https://arxiv.org/abs/1810.05045 | When fixed resampling fails | Fixed operators | L–M |
| Antipov & Doerr 2025, IJCAI | https://www.ijcai.org/proceedings/2025/983 | (1+1) EA without re-evaluation is more robust | Fixed mutation operator | **M–H** |
| Smith & Winkler 2006, Mgmt Sci 52(3) | https://ideas.repec.org/a/inm/ormnsc/v52y2006i3p311-322.html | The optimizer's curse; Bayesian shrinkage | One-shot selection | **H** (C2-iv concept) |

## 6. Winner's curse, model selection, adaptive data analysis
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| Cawley & Talbot 2010, JMLR 11 | https://www.jmlr.org/papers/v11/cawley10a.html | Overfitting in model selection | One-shot / nested CV | M |
| Dwork et al. 2015, Science 349 (reusable holdout) | https://cis.upenn.edu/~aaroth/reusable.html | Adaptive holdout reuse via DP | Covers adaptive analysts | M |
| Blum & Hardt 2015, ICML (arXiv 1502.04585) | https://www.arxiv.org/abs/1502.04585 | The Ladder: update the record only on a margin beat, under adaptivity | Closest classical keep rule | **H** (C2-i/iv) |
| Andrews, Kitagawa & McCloskey 2024, QJE 139(1) | https://ideas.repec.Org/a/oup/qjecon/v139y2024i1p305-358..html | Inference on winners | One-shot | M |

## 7. Decision-focused learning; RL post-training of LLM predictors
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| Elmachtoub & Grigas, arXiv 1710.08005 (SPO+) | https://arxiv.org/abs/1710.08005v2 | SPO loss and convex surrogate | Linear objective | M |
| Wilder, Dilkina & Tambe 2019, AAAI 33 | https://ojs.aaai.org/index.php/AAAI/article/view/3982 | Decision-focused learning via relaxation | Not RL | M |
| Mandi et al. 2024, JAIR 81 (arXiv 2307.13565) | https://arxiv.org/abs/2307.13565v4 | DFL survey and benchmark | — | M |
| Park et al. 2025, arXiv 2511.04393 | https://arxiv.org/abs/2511.04393v1 | Regret-minimisation fine-tuning of LLM agents | LLM as actor, not a predictor feeding a rule | M |
| Turtel et al. 2025, arXiv 2505.17989 | https://arxiv.org/abs/2505.17989 | RLVR for LLM forecasting | Exogenous events | M |
| Turtel et al. 2026, arXiv 2608.28482 | https://arxiv.org/abs/2608.28482 | Proper scoring rules shape LLM forecasting | — | M (Brier vs log reward) |
| Yaldiz et al. 2026, arXiv 2601.13284 | https://arxiv.org/abs/2601.13284 | RLVR overconfidence; SFT calibrates better | — | M (supports SFT-first ladder) |

## 8. LLM-specific (novelty-critical)
| Work | Verified | What it does | Assumes / covers | Overlap |
|---|---|---|---|---|
| LLAMBO, arXiv 2402.03921 | https://arxiv.org/abs/2402.03921v2 | LLM surrogate / sampler in BO, in-context | No fine-tuning, no noisy incumbent | M |
| Zhang et al. 2023 (LLMs for HPO) | https://research.nvidia.com/publication/2023-12_using-large-language-models-hyperparameter-optimization | LLM proposes hyperparameters / code | No noise handling | L–M |
| Jawahar et al. 2023, arXiv 2310.16712 | https://arxiv.org/abs/2310.16712v1 | LLM performance predictor distilled for NAS screening | Architectures, not incumbent-relative increments | M |
| Hao, Zhang & Zhou 2024, arXiv 2406.10675 | https://arxiv.org/abs/2406.10675 | LLM as surrogate for pre-evaluation selection | Inference only | M |
| Wen et al. 2025, arXiv 2506.00794 | https://arxiv.org/abs/2506.00794 | Fine-tuned LLM predicts which research idea wins | Pairwise, no control rule | M–H |
| **Zheng et al. 2026, FOREAGENT, ACL 2026 (arXiv 2601.05930)** | https://aclanthology.org/2026.acl-long.182/ ; https://arxiv.org/abs/2601.05930 | Pairwise solution preference (18,438 pairs, 61.5 %); Predict-then-Verify loop | **Nearest prior for C3.** Pairwise, no increment distribution, no noise/seed model, no decision-theoretic threshold (abstract) | **H** |
| **Wang et al. 2026, SAGE, arXiv 2609.36043** | https://arxiv.org/abs/2609.36043 | Per-item paired one-sided test vs incumbent; cites the optimizer's curse | **Nearest prior for C1/C2 in agent loops.** Item-level noise, frequentist test, no prior / screening / run price (abstract) | **H** |
| He et al. 2026, Beneath the Diff, arXiv 2609.00077 | https://arxiv.org/abs/2609.00077 | Same keep-if-better ML-edit loop; repetitive edit types; DAPS (coverage reweighting, edit memory, validation gate) | No noise model or learned prior (abstract) | **H** (C1 waste; memory-reading proposer) |
| Oved et al. 2026, arXiv 2609.19799 | https://arxiv.org/abs/2609.19799 | Seeds-by-iterations frontier; rankings flip with budget | Reporting protocol | M |
| Papamarkou et al. 2026, arXiv 2606.24453 | https://arxiv.org/abs/2606.24453 | Bayesian cost-sensitive gather/refine/verify/stop for coding agents | Binary correctness | M |
| Chen & Yi 2026, arXiv 2606.01730 | https://arxiv.org/abs/2606.01730 | Evidence-gated LLM priors for BO | Molecules | M |
| Shi et al. 2026, EarlyEval, arXiv 2609.02783 | https://arxiv.org/abs/2609.02783v1 | LightGBM mid-run outcome prediction | Evaluation cost | L–M |
| Toledo et al. 2025, arXiv 2507.02554 | https://arxiv.org/abs/2507.02554 | Search policies for MLE-bench | — | L |
| Jain et al. 2026, AutoResearch-RL, arXiv 2603.07300 | https://arxiv.org/abs/2603.07300 | RL over code edits | No noise treatment (abstract) | L |
| Qu & Lu 2026, Bilevel autoresearch, arXiv 2603.23420 | https://arxiv.org/abs/2603.23420 | Outer loop injects search mechanisms | — | L–M |
| Jeddi et al. 2026, GEAR, arXiv 2605.13874 | https://arxiv.org/abs/2605.13874 | Population search instead of single incumbent | — | L–M |
| Li 2026, arXiv 2603.15916 | https://arxiv.org/html/2603.15916 | 10,469 LLM-run experiments; score + noise model | Descriptive | L |
| Karpathy, autoresearch | https://github.com/karpathy/autoresearch | Keep-or-discard on val_bpb | Default rule | context |

**Novelty-critical answer.** No work found (abstract level) with all three of: LLM proposer + noisy incumbent-relative acceptance + learned per-proposal prior / pre-execution screening. SAGE has the first two, FOREAGENT the first and third, Beneath the Diff the loop + memory + gate without a statistical model. All are 2026; reviewers will know them.

## What classical results assume vs the governed loop
1. Fixed, known arm set (R&S, BAI, KG); relaxed only by Hong & Nelson 2007 and reservoir bandits.
2. i.i.d. generation from a fixed reservoir / fixed mutation operator; the proposer here is ledger-dependent.
3. Free resampling of any arm incl. the incumbent; here verify spends the same run budget as new proposals (priced sampling in Chick–Inoue, Chick–Frazier, Xie–Frazier is per existing alternative, not traded against new proposals).
4. Known/fixed standard or threshold; here the standard is a moving, upward-biased recorded maximum (bias treated only one-shot or in GP settings).
5. No restore / roll-back semantics; the Ladder is the closest match.
6. No proposer feedback (except adaptive data analysis; Beneath the Diff shows memory-driven repetition empirically).
7. Single noise source per arm; here seed and split noise, and verify resamples only some (CRN/blocking analogues).
8. No pre-execution information per arm; content-conditional priors only in LLM work, none tied to a Bayes-optimal keep rule.

## Novelty verdict per claim
| Claim | Risk | Nearest prior | Differentiator to defend |
|---|---|---|---|
| C2-i Bayes keep threshold | **High** | Xie & Frazier 2013; Chick & Frazier 2012; Smith & Winkler 2006; Blum & Hardt 2015; Jin & Branke 2005 | Threshold on the increment over a noisy, restored, biased record; error rates measured (C1). Present the formula as an instantiation, not a contribution. |
| C2-ii/v verify VoI and run-price index | **High** | KG 2008; Chick & Inoue 2001; Chick & Frazier 2012; Papamarkou et al. 2026 | Verify competes with **new proposals** for one run budget and resamples only part of the noise. "Verify rarely pays" follows from the proposal-supply term. |
| C2-iii verify corrects only resampled noise | Medium | Nelson & Goldsman 2001; F-Race; Bouthillier 2021 | Explicit decomposition into resampled vs frozen error, measured. |
| C2-iv winner's curse for any adaptive proposer | Medium | Smith & Winkler; Andrews et al.; Zhou et al.; Wang et al. 2025; Antipov & Doerr; **SAGE**; Dwork et al. | Inverse-Mills bound conditional on an arbitrary adaptive proposal law, plus the induced acceptance fall. |
| Per-proposal prior, gain decomposition, skip rule | Medium | correlated KG; LLAMBO; Hao et al.; Jawahar et al.; **FOREAGENT**; Chen & Yi | How much a content-conditional prior can gain (threshold dispersion) and the optimal skip rule under a run price; prior LLM predictors give pairwise preferences with no rule or bound. |
| Decision independence / myopic optimality | Low–Medium | KG one-step results; Chick & Frazier (DP beats one-step); Hong & Nelson; Beneath the Diff | Condition on the proposer's dependence on decisions; counterexample for a ledger-reading proposer. |
| C3 SFT → decision-focused GRPO ladder | Medium | **FOREAGENT**; Wen et al.; Turtel et al.; Park et al.; Yaldiz et al.; DFL | Fresh-seed-audited increment labels; reward = downstream decision regret under the theory rule; gain over proper-score SFT located where threshold dispersion predicts. No prior found doing decision-focused RL post-training of an LLM predictor feeding an accept/skip rule. |

## Baselines this implies
1. Strict-beat-record (default) and Ladder-style margin beat (tuned margin).
2. **SAGE-style paired one-sided test gate.**
3. Re-evaluate incumbent vs never (Antipov & Doerr; Qian et al.).
4. Posterior-mean incumbent (Wang et al. 2025; Zhou et al. 2024; NEI).
5. KG / EVI verify; Chick–Frazier one-vs-standard sequential sampling with cost.
6. Comparison-with-a-standard (Kim 2005); OCBA on the retained set.
7. Racing / intensification (SMAC intensifier; irace elitist racing).
8. Thresholding / good-arm identification with the record as threshold.
9. Pre-execution predictors: LLM zero-shot; LLAMBO-style in-context surrogate; **FOREAGENT-style pairwise predict-then-verify**; LightGBM; distilled LLM regressor; rule-based duplicate/no-op filter.
10. Proposer-side alternatives: GEAR population search; DAPS (Beneath the Diff).

## Could not verify
- Bechhofer 1954 (listing only).
- **arXiv 2610.15738, "Visible but Not Avoided: State-Dependent Re-Proposal of Rejected Candidates in Catalog-Based LLM Optimization Loops"** (listing only; HTTP 429) — possibly directly relevant to the ledger-dependent proposer; check manually.
- Venues seen in listings only: Elmachtoub & Grigas (Mgmt Sci "forthcoming"); Kano et al. (ML 108); LLAMBO (ICLR 2024); Wen et al. (NeurIPS 2025); Jawahar et al. (ACL Findings 2024); Kaufmann et al. (JMLR 17); Birattari et al. (GECCO 2002).
- Kim & Nelson 2001 abstract not available.
- Internals not in abstracts: NEI incumbent; SMAC/ParamILS intensification; SAGE noise model; FOREAGENT training and seed handling. Full texts of the 2026 autoresearch papers not read.
