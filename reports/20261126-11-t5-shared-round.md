# local/20261126-11 — T5 shared-noise: the one correction round (DONE)

- **Task:** `local/20261126-11`
- **Branch:** `mac-t5-shared-20261122`. New tip **`440a3dd9`**: one commit on `d0ef5282`.
- **Review:** `docs/r1/reviews/T5_SHARED_NOISE_REVIEW_20261126.md` (`coord-reviews-20261126` @ `a2464ec4`), ACCEPT WITH MINOR. Tier S: one round, with no further review.
- **Files:** one file changed, `docs/r1/theory/T5_SHARED_NOISE_20261122.md`. Code, parts and tables are unchanged.

## Minors

- **m1:**
  - The §5 row now separates the bases.
    - Oracle-prior: +1.84 δ_n oracle and +0.47 δ_n feasible.
    - A2: +3.27 δ_n and +1.38 δ_n.
    - Both at digits_on, W = 20, s = 0.79.
  - It adds A2's range over the four cells (digits_on and digits_off × W = 20 and 40): +1.4 to +5.7 δ_n feasible and +3.3 to +10.0 δ_n oracle. I checked these against `tables.md`: 1.38/4.12/2.10/5.70 and 3.27/8.06/4.17/9.97.
  - **For the author (via the coordinator):** PLAN row R1-D3-CHOICES (1) quotes "+0.47 … to +1.84 δ_n" as A2's. Those are the oracle-prior base's figures. Draft fix for the row: "… sizes the gain from correcting the threshold on `digits_mlp` (digits_on, W = 20) at +0.47 δ_n (feasible) to +1.84 δ_n (oracle) for the oracle-prior base, and +1.38 to +3.27 δ_n for A2 (+1.4 to +5.7 feasible, +3.3 to +10.0 oracle over the four cells)". The decision in the row does not depend on the size. I did not edit PLAN.
- **m2:** "upper bound / lower bound / the Bayes correction lies between" is now an **empirical bracket**: table < known in all 48 shared and record cells. It also says each rule is myopic, neither is campaign-optimal, and neither is Bayes for A2 (misspecified plug-in). The §6 limit line is changed to match.
- **m3:** "as R1-THEORY-RHO (2) states" is now "consistent with R1-THEORY-RHO (2): on average over the type mix". The note gives (2)'s conditions and says the figures do not test (2) per proposal.

## Notes, one line each

- **n1:** no change. The note already says the kernel-free check tests the code, not the claim.
- **n2:** added after the kernel-free table. The `main` paraphrase of R1-THEORY-RHO (1) holds only for t ≥ 0. It fails on 23–32 % of keeps with negative t, so text quoting (1) should keep the t ≥ 0 condition.
- **n3:** no change. The common-u assumption of the branch-study equivalence is already stated as a limitation; the review found that sufficient.
- **n4:** provenance sentence added: `git_head_at_write` is the merge base, the source hashes match, and the review's re-run reproduced the parts.
- **n5:** no change. It is a confirmation, not a finding.
- **n6:** the status line now cites the review. The grid edges were already disclosed.

## Tests

`python -m pytest -q -p no:cacheprovider r1/tests/test_t5_shared_noise.py` → **8 passed**.

## Next

The coordinator merges the unit, and brings the R1-D3-CHOICES (1) wording to the author.
