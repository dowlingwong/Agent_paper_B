# Build P4 — executor response to review round 2 (16 Nov 2026)

ENGINEERING_ONLY. Review: `BUILD_P4_REVIEW_20261116.md`, Round 2 (NOT ACCEPTED, 1 MAJOR / 4 MINOR). The ladder table was rebuilt (the oracle table is unchanged: no simulator change); the report was revised.

| # | Finding | Change |
|---|---|---|
| R2-1 | N2b's budget-world gain is a dev-draw artefact | N2b's heads read belief outputs only: E1 [1, V\*, τ], E2 [1, m̂]; no budget features, so a cut tuned on terminal value can no longer turn the head into a budget rule; N2b is single-step in target and form; report §3.2 rewritten |
| R2-2 | RawKeep is only the no-shrinkage corner | new tuned reference row `ShrinkRefit` (keep on a + min(λk, 1)(Δ̂ − a), λ tuned from 1 = the belief's m̂; the reviewer's form), charged like the other rows; `RawKeep` kept as its corner; test `test_shrink_refit_corners`; report §1, §3 reworded ("belief refit" = the ShrinkRefit row) |
| R2-3 | the one-se move rule lets noise moves through | stated in `policies.py` and the report (null: N1 and N3 move off the Bayes rule; N3 −0.00007 ± 0.00004 on test); the rule is kept; a stricter rule or split-dev confirmation is noted as an option for SPT-5 |
| R2-4 | "no rung reads the raw increment" too strong; response error | wording: no rung's **keep decision** reads Δ̂; SPRT and racing read the mean increment at the verify epoch as their test statistic; the test is renamed and documented accordingly; correction to response R1: N2b's cut is not charged the coarse grid (only N1, N2, N3, margin, B18, RawKeep and ShrinkRefit are) |
| R2-5 | §3.10 random_N1 "worst" | reworded with the rows that are worse |

## After round 3 (ACCEPT)

R3-1 (wording): the budget-world "ties" are now stated as negligible gains whose intervals exclude 0; §3.6 reads 0.0008–0.0011; §3.9 says the raw-keep gain is consistent with over-strong shrinkage under the shared incumbent error and equally with the winner's-curse bias of the incumbent record.
