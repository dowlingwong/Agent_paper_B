# Prompt — independent review of Track S runbook, revision 2 (29 Oct 2026)

You are a **fresh, independent reviewer** with no prior context on this project. Review it as a skeptical ICML reviewer from the dynamic algorithm configuration (DAC) / RL community would, and with the care of an experimental statistician. Work **read-only**. Do not change the runbook. Do not start runs, SSH, LLM calls or commits. The only file you write is your review.

## Background (minimum you need)

Paper B (repo `/Users/wongdowling/Documents/agent_paper_B`, route R1) studies a governed LLM-driven autoresearch loop:
- An LLM manager proposes one-parameter edits to an ML training configuration.
- A control plane decides **execute/skip at E1** and **keep/discard at E2**, against an incumbent, under noisy metrics.
- The budget is worker runs W plus an LLM-call cap.

The paper's headline is "noise-aware dynamic algorithm configuration". A revised theorem (T4 Prop. 10(a′)) says that, with a fixed run price g, no feedback (NF) and no information (NI), the myopic index rule is globally optimal. The loop then decouples into one-step decisions.

Track S is a proposed experiment to decide between three outcomes:
- **route A:** sequential structure matters, so keep the DAC framing and the multi-step/RL arms;
- **route B:** within a margin, the loop behaves as one-step decisions on the most favourable affordable nodes, so reframe;
- **inconclusive.**

Revision 1 was reviewed and got 3 BLOCKING and 7 MAJOR findings. Revision 2 claims to address all of them; its §11 maps each finding to a resolution.

## Files to read

In the repo:
- `docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`: **the document under review** (rev. 2).
- `docs/r1/proposals/TRACK_S_REVIEW_20261029.md`: the review of rev. 1.

Planning and theory docs. The newest versions are on branch `docs/c3-pool-28oct`; read them with `git show docs/c3-pool-28oct:<path>` rather than from the working tree, which is on `exam-x-20261026`:
- `docs/r1/PLAN.md` (§10 dated decision rows, e.g. D18, "g (22 Oct)", R1-ROUTE-DAC, R1-C3, the C3 gate);
- `docs/r1/proposals/T4_PROP10_REVISION_20261028.md` and `docs/r1/reviews/T4_PROP10_REVISION_REVIEW_20261028.md`;
- `docs/r1/C3_DESIGN.md`, `docs/r1/TRACK_P_POST_TRAINING.md`, `docs/r1/RUNBOOK.md`, `docs/r1/STATUS.md`;
- `docs/r1/reports/DI_TEST_*_20261019.md`, `NOISE_FLOOR_COMMON_20261022.md`, `DUPLICATE_RATE_PILOT_20261022.md`.

Code:
- `r1/c3/` (`control.py`, `env.py`, `features.py`, `rules.py`, `offline_eval.py`) and `r1/headroom/e1b_collect.py`.
- Harness: `/Users/wongdowling/Documents/autoresearch_harness`, **branch `r1`**. Read with `git show r1:<path>` if the working tree is on another branch. Key files are under `src/autoresearch/`: `control_plane/campaign.py`, `control_plane/snapshot.py`, `control_plane/controller.py`, `memory/summarizer.py`, `manager/langgraph_manager.py`, `budget.py`, `local_worker.py`, `llm/providers.py`. Node definitions are in `nodes/`.

## Tasks

1. **Check the rev-1 resolutions.** For every row of rev. 2 §11, give ACCEPT, PARTIAL or REJECT, with one line of reasoning. Do not take the table's word for it; check the body text.
2. **Spot-check facts.** Check at least 6 claims in §1 against the code or reports at file:line. Report any that are wrong, stale or overstated.
3. **Fresh review of rev. 2.** Look especially at the following.
   - **Primary estimand I_seq (§3, §6 S3b).** Is it well defined and identified? Specifically:
     - π′ combines the myopic controller's one-step estimate with a fitted continuation contrast Ĉ(s). Are the two on the same scale, given that terminal Y is the final incumbent's audited value and not a sum of increments?
     - Does "continuation = measured Q − audited immediate part" make sense under non-additive Y?
     - Is cross-fitting at instance level, with IPW for the near-threshold oversample, correctly specified?
     - Does keeping the myopic one-step estimate really remove credit for plain miscalibration?
   - **Margins.** Is δ_Y = max(0.002, 0.1 × E[Y_myopic − Y_start]) sensible? Is the per-decision margin δ_dec = δ_Y / k_n defensible, or is it too lenient or too strict?
   - **Channel arms (skip / ghost / controller-only / execute).** Can the harness implement these through `resume_campaign` overrides as claimed?
     - Do skip, ghost and controller-only really present identical manager prompts?
     - Is the seen-set (duplicate filter) placed in the right arm?
     - Do Δ_B, Δ_I and Δ_F identify budget, information and feedback, or do interactions and path divergence confound them?
   - **Decision rule.** Is it symmetric and pre-declarable, and is it free of post-hoc escape routes?
     - Holm over two nodes;
     - route B needing both nodes and the controls;
     - the voiding rules;
     - whether "inconclusive" is honestly worded.
   - **Controls.** Are the synthetic positive controls (Prop. 10(b), 10(c)) and the negative control (NF + NI) faithful to the theory and run through the same pipeline? Could they pass while the real-node pipeline is still broken?
   - **Power and feasibility.** Use σ_node, about 7–10 informative decisions per campaign, about 2.5 s per run, and a serial LLM. Is about 300 forks per node and 36k LLM calls per node realistic? Is the target before ~22 Nov realistic, given that code and review must land by ~5 Nov?
   - **Hindsight bound U, the per-trial-seed check, and S3c** (learned multi-step baseline). Are they correct and useful, or could they be cut?
   - **DAC lens.** Would route A or route B, as defined here, convince a DAC/RL reviewer? What is still missing?
   - **Over-engineering.** What could be dropped without weakening the decision?
4. **Verdict:** ACCEPT, ACCEPT WITH MINOR CHANGES, or REVISE. If REVISE, list exactly what blocks acceptance.

## Output

Write `docs/r1/reviews/TRACK_S_REV2_REVIEW_20261029.md`:
- English;
- headed "AI-assisted review (fresh agent); read-only; authorizes nothing";
- under about 1,500 words, excluding the §11 table and the fact-check table;
- findings ordered by severity (BLOCKING / MAJOR / MINOR), each with a concrete fix;
- every factual claim cited at file:line.

Then reply with a short summary: the verdict, a count by severity, and the top three issues. Do not commit and do not edit any other file.
