# Prompt — independent review of Track S runbook, revision 3 (29 Oct 2026)

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

Revision 1 got 3 BLOCKING and 7 MAJOR findings. Revision 2 got REVISE, with 3 BLOCKING, 6 MAJOR and 6 MINOR (`docs/r1/reviews/TRACK_S_REV2_REVIEW_20261029.md`). Revision 3 claims to address the revision-2 findings; its §11 maps each one to a resolution. Its main changes are:
- a Bayes-updating base controller, A2-U;
- action scores that combine a forecast immediate value with the measured continuation;
- a decision rule π′ with no price g, benchmarked against a re-fitted static price;
- a split-repetition guard U_split for route B;
- a W chosen so that the budget binds;
- an online confirmation S3d;
- zhixu portal as the host (PLAN §10 R1-TRACKS-HOST).

## Files to read

In the repo:
- `docs/r1/proposals/TRACK_S_SEQUENTIALITY_RUNBOOK_20261029.md`: **the document under review** (rev. 3).
- `docs/r1/reviews/TRACK_S_REV2_REVIEW_20261029.md`: the review of rev. 2.
- `docs/r1/proposals/TRACK_S_REVIEW_20261029.md`: the review of rev. 1 (background).
- The R1-TRACKS-HOST row is in the **working tree** of `.claude-worktrees/c3-pool-28oct/docs/r1/PLAN.md` (uncommitted), not in the branch commit.

Planning and theory docs. The newest versions are on branch `docs/c3-pool-28oct`; read them with `git show docs/c3-pool-28oct:<path>` rather than from the working tree, which is on `exam-x-20261026`:
- `docs/r1/PLAN.md` (§10 dated decision rows, e.g. D18, "g (22 Oct)", R1-ROUTE-DAC, R1-C3, the C3 gate);
- `docs/r1/proposals/T4_PROP10_REVISION_20261028.md` and `docs/r1/reviews/T4_PROP10_REVISION_REVIEW_20261028.md`;
- `docs/r1/C3_DESIGN.md`, `docs/r1/TRACK_P_POST_TRAINING.md`, `docs/r1/RUNBOOK.md`, `docs/r1/STATUS.md`;
- `docs/r1/reports/DI_TEST_*_20261019.md`, `NOISE_FLOOR_COMMON_20261022.md`, `DUPLICATE_RATE_PILOT_20261022.md`.

Code:
- `r1/c3/` (`control.py`, `env.py`, `features.py`, `rules.py`, `offline_eval.py`) and `r1/headroom/e1b_collect.py`.
- Harness: `/Users/wongdowling/Documents/autoresearch_harness`, **branch `r1`**. Read with `git show r1:<path>` if the working tree is on another branch. Key files are under `src/autoresearch/`: `control_plane/campaign.py`, `control_plane/snapshot.py`, `control_plane/controller.py`, `memory/summarizer.py`, `manager/langgraph_manager.py`, `budget.py`, `local_worker.py`, `llm/providers.py`. Node definitions are in `nodes/`.

## Tasks

1. **Check the rev-2 resolutions.** For every row of rev. 3 §11 ("Revision 2 → 3"), give ACCEPT, PARTIAL or REJECT, with one line of reasoning. Do not take the table's word for it; check the body text.
2. **Spot-check facts.** Check at least 6 claims in §1 against the code or reports at file:line. Report any that are wrong, stale or overstated.
3. **Fresh review of rev. 3.** Look especially at the following.
   - **A2-U** (§3).
     - Is a per-key conjugate normal update a reasonable stand-in for the theorem's Bayes-myopic rule?
     - Can S0.4's dev campaigns (10 instances per node, execute-all) fit its prior honestly?
     - Does using A2-U instead of the deployed A2 change what Track S can say about the paper's C3 comparator?
   - **Scoring and π′.**
     - Scoring: score(a) = forecast immediate value + measured continuation, with no price, the run's cost sitting inside the continuation because the run is debited. Does this remove credit for one-step heterogeneity and miscalibration?
     - Is "continuation = terminal Y − measured immediate part" well defined when Y is the final incumbent's audited metric?
     - Is π′ (execute iff V̂* + Ĉ > 0) vs m_ĝ at ĝ_fold = −mean(C_exec − C_skip) coherent?
   - **U_split.** Is it unbiased under the null as claimed? Does it close the route-B escape?
   - **Inference.** Are the 5-fold instance-level cross-fitting and the refitting cluster bootstrap correctly specified, given IPW and pooled E1/E2 forks?
   - **Binding W.** Is choosing W from S0.5 (largest W in {8, 10, 12, 20} that binds in ≥ 50 % of campaigns) sound? What does the departure from deployment W = 20 cost?
   - **Channel arms.** Ghost and controller-only on a random third of E1 forks. Are the four arm-invariance tests sufficient?
   - **Margins and power.** δ_Y = max(0.002, 0.5 σ_node) in raw metric units and δ_dec = δ_Y / k_n. Are they sensible and achievable at the fork counts implied?
   - **Controls.** Do P1 (shared key), P2, N0 (non-binding W) and the real-node budget control (Δ_B > 0 at a binding W) make route B symmetric? Can they pass while the pipeline is broken?
   - **S3d online confirmation.** Is its rule sensible? Is it feasible?
   - **Schedule.** Check the cost model by latency, the one-node fallback, and the date (results ≈ 18–20 Nov if latency ≤ 3 s).
   - **DAC lens and over-engineering.** Would route A or route B convince a DAC/RL reviewer now? What can still be cut?
4. **Verdict:** ACCEPT, ACCEPT WITH MINOR CHANGES, or REVISE. If REVISE, list exactly what blocks acceptance.

## Output

Write `docs/r1/reviews/TRACK_S_REV3_REVIEW_20261029.md`:
- English;
- headed "AI-assisted review (fresh agent); read-only; authorizes nothing";
- under about 1,500 words, excluding the §11 table and the fact-check table;
- findings ordered by severity (BLOCKING / MAJOR / MINOR), each with a concrete fix;
- every factual claim cited at file:line.

Then reply with a short summary: the verdict, a count by severity, and the top three issues. Do not commit and do not edit any other file.
