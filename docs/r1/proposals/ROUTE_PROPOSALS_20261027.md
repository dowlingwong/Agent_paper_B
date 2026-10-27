# Route proposals for the author — 27 October 2026

AI-assisted. These are questions and recommendations, not decisions, authorizations or evidence. Line references below identify the scanned revision `ad90149`, before later historical annotations shifted lines; stable row names identify the controlling decisions. The relevant statements and historical conflicts are inventoried in `docs/r1/reports/LOCAL_CONSISTENCY_SCAN_20261027.md`. PLAN §10 remains authoritative until the author decides and the coordinator records any decision.

## R1 — Headline framing: DAC or noise-aware agent control?

`PLAN.md:22` adopts noise-aware learned control and says DAC is related-work vocabulary only. `PLAN.md:474` adopts a DAC interface, but does not itself replace that framing. The author requested that the paper be framed as a DAC problem; the exact headline decision remains to be recorded.

- **A: DAC headline.** Frame the governed loop as dynamic algorithm configuration under noise, with contextual-bandit per-proposal decisions and sequential feedback. Consequences: DAC baselines, instance generalisation and the distinction from classical DAC become central review obligations; the theory and measured noise mechanism must still be explicit.
- **B: Noise-aware agent-control headline.** Retain R1-ROUTE and use DAC as the formal interface and related-work connection. Consequences: emphasizes acceptance and screening under noise; the paper still needs to compare relevant DAC work and explain sequential feedback.
- **Recommendation:** A, given the author's stated preference, subject to a dated PLAN row. Write the problem formulation so the eventual decision does not imply that unmeasured feedback or results are established.

## R2 — Bin edges and no-op semantics

`C3_DESIGN.md:40` and `TRACK_P_POST_TRAINING.md:124–126` list different numerical edges; the latter asks for confirmation (`:410`). Options: preserve the currently implemented version as the canonical protocol after verifying its provenance, or adopt a separately versioned alternative with explicit migration and comparisons. **Recommendation:** inspect the existing committed labels, frozen rules and training code first, then author-select and record one version; do not alter existing data or backfill outcomes. A mismatch can change labels, heads and calibration.

## R3 — Hard-label exceptions

R1-C3-POST prohibits hard labels for training (`PLAN.md:490`), while the Track P specification describes a hard-label synthetic E0 contrast and real-label ablation (`TRACK_P_POST_TRAINING.md:261,387`). A binary execute/skip action target (`:347`) is a different object from a hard belief target.

Options: explicitly authorize the synthetic contrast and/or real-label ablation as bounded diagnostic exceptions, or remove those belief-training contrasts from the planned evaluation. **Recommendation:** decide the synthetic and real-label cases separately and state how each is labelled and gated; never interpret this proposal as permission to train.

## R4 — R-A0 decision rule

`TRACK_P_POST_TRAINING.md:151` reserves a bin-level shortcut for R-A3, while `:318` assigns it to R-A0. Options: use the adopted moments-based `rules.decide` path for R-A0, or explicitly adopt a versioned bin-level value rule and its price convention. **Recommendation:** use the existing moments-based path unless the author adopts an alternative; specify where g enters and verify equivalence or differences before evidence.

## R5 — RPS normalization and reward scaling

The specification sums cumulative errors and a separate no-op term (`TRACK_P_POST_TRAINING.md:296`) but states a bound of at most one (`:353`), which is not established by that definition. Options: retain the sum and derive its actual bound with explicit reward scaling, or adopt a normalized score and rescale its coefficients. **Recommendation:** derive and verify the bound for the exact implementation, then author-select the version before freezing any reward; changing scaling can change the objective.

## R6 — Shared representation and belief/action separation

R-A2 lets the action loss update shared LoRA while the belief output uses a proper-score loss (`TRACK_P_POST_TRAINING.md:320,330`); the reasoning arm can also couple action policy and the context used by the belief (`:349–354`). Options: treat this as an explicitly monitored shared-representation ablation, or require detached updates for stricter separation. **Recommendation:** retain both proposed arms only if the author confirms this interpretation and specifies what constitutes acceptable belief drift; no threshold or objective is changed here.

## R7 — DI endpoint and interpretation

The partial-arm row permits absolute metrics or audited values and forbids branch-relative Δ̂ (`PLAN.md:421`); T5's model says even absolute outcomes can contain incumbent effects and identifies an audited increment over each branch's incumbent as cleaner under its assumptions (`theory/T5_SIMULATION.md:123–127`). Options: preserve the authorized partial diagnostic as descriptive and predeclare a separate audited-increment endpoint for future analysis, or retain absolute outcomes with a clearly scoped sensitivity analysis. **Recommendation:** separate the historical partial diagnostic from a prospective endpoint decision; do not treat the simulation as a causal finding or silently reinterpret the author row.

## R8 — Track H.8 coordination

RUNBOOK H.8 says action = bin (`RUNBOOK.md:176`), while R1-C3-POST separates the 12-bin belief from execute/skip actions (`PLAN.md:490`). Options: coordinator approves a narrowly scoped H.8 implementation change after a written design and tests, or leaves the existing environment untouched until the Track P owner coordinates it. **Recommendation:** coordinate the interface and ownership first. The Mac agent must ask before editing `r1/c3/env.py`, `control.py`, `serve.py` or `prior_model.py` and must not edit `r1/c3/train/`.

## R9 — Theory and framing claims

T1 describes feedback as intrinsic (`theory/T1_MODEL.md:42`), while T4 states DI as a possible condition (`theory/T4_FEEDBACK_PROPOSER.md:99–105`). Track P calls DAgger evidence for feedback (`TRACK_P_POST_TRAINING.md:49`). Options: present feedback and DAgger as hypotheses requiring measurement, or propose a stronger, specifically justified claim after the proof and empirical checks. **Recommendation:** use the former until checked. This question does not resolve the proof audit or author proof check.
