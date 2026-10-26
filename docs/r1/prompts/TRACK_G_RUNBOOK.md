# Track G remote runbook — proposal for author decision

**PROPOSAL, 27 October 2026.** This file authorizes no remote command, model access, container use, evidence run, budget, protocol change or merge. RUNBOOK G.1–G.5 and the current PLAN §10 rows govern. L4.1 is not accepted: see `docs/r1/reviews/LOCAL_L4_1_REVIEW_20261027.md` and the three isolated `r1-local-*` harness branches. The adapters and their safe stub campaigns must pass independent review before any proposed evidence phase.

## G.2: container access and evaluator provenance

The author/coordinator establishes whether the MLGym tasks can run in an approved container on deepthought or the zhixu portal, records access, task version, evaluator digest and required data provenance, and decides whether to drop MLGym if unavailable. Obtain and verify an authoritative 1GC-7RC task source, evaluator, license and revision before implementing its four adapters; the currently inspected paper is insufficient to establish executable contracts. Decide whether the restricted edit scope and the T5/T6 upstream held-out scoring split are suitable for repeated proposal selection. No test-set selection policy is adopted by this proposal.

## G.3: proposed noise-floor preparation

For each approved node, pre-declare the configuration, metric and direction, seed blocks, determinism and training/split noise measurements, run cost, sampling count and failure handling before measuring. The number of seeds and any reduced budget require author approval. RUNBOOK G.3 names the zhixu portal, with resumable autoresearch overflow on zhixu experiment; the Mac runbook also requests Ada overflow under R1-ADA-OVERFLOW. Reconcile the intended assignment with the author while preserving the decided host/table comparability constraints. A host or GPU change is not inferred from this document. Commit provenance, raw measurements, results and independent review before proposing noise-floor rows.

## G.4: author choice

Choose whether the new nodes are evaluation/transfer only or receive small label sets, and set their audit budget and effect on claims. Record the adopted choice in PLAN §10 before applying it; alternatives and consequences must be documented without using held-out outcomes to select a design.

## G.5: proposed transfer evaluation

After the applicable earlier gates and G.4 decision, pre-declare instances, arms, selection and audit seed separation, matching, resource budgets, analysis, and failure handling for the intended A1–A6 transfer comparison. Freeze the declaration and its hash before data collection. Preserve a single declared hardware/environment identity for each comparison table unless the governing PLAN row explicitly permits otherwise. Execution, analysis and adoption each require their applicable author/coordinator authorization and independent review.

## Open questions

1. Can the coordinator provide authoritative, revision-pinned 1GC task code and decide how its test-scored tasks can be used without test-set selection?
2. Which host and container setup is approved for G.2 and G.3 under current host-availability and overflow decisions?
3. What role and audit budget should Track G have, and which approved comparisons and seed counts should be pre-declared?
