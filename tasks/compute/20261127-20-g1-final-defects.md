# compute/20261127-20 — D.3 G1: two final-snapshot defects found in revision 4's step-(5) review (blocks freezing)

Owner: compute (G1 is yours). Runbook §2 order 2A. Base: `main` `c4250f7e`. Read `docs/r1/reviews/D3_PREDECL_R4_STEP5_REVIEW_20261127.md` and
`docs/r1/reports/d3_predecl_r4_step5_20261127/REPRODUCTIONS.md` (both on `main`).

1. **Harness arms, `final.json`.** With the real pinned harness `9bb41680` and a synthetic worker, a keep on trial 20 (worker-run cap) and a
   keep on trial 7 (early LLM-call cap) gave `final.json` keep 19 and 6 and a config hash other than the actual last kept incumbent. The at-W
   alias copies a pre-E2 snapshot; the below-W branch takes the last E1 capture. Fix: `final.json` is written from the incumbent after the
   last E2 decision (as the replicate route's post-decision final does), and a w snapshot taken before a decision is never aliased as final.
2. **Replicate route.** For an EGATE-shaped trace, the live charge snapshot audited `y_raw = 0.50` and the post-decision final `0.70`, and G6
   sealed both. G7 and the pinned analysis correctly refused the pair (draft §7.5(a)/§8). Make the at-W record and the final the same
   configuration when they denote the same point (the final governs), so that one audit serves both, as the design's alias rule intends.
Keep the four conditions of `compute/20261127-04`. Add both reproductions as tests (they fail before and pass after). Full suite at harness
`9bb41680` with zero new failures; fresh tier-E review. Then the local worker repeats step (5) (`local/20261127-16`). No change to G6, G7
or the analysis script unless the review shows they must change. If so, say why, because their hashes are pinned in revision 4.
