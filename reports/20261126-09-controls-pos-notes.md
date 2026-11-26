# local/20261126-09 — positive control: re-check notes N1–N4 fixed (DONE)

- **Task:** `local/20261126-09`
- **Branch:** `mac-controls-pos-20261123`. New tip **`70af1457`**: one commit on top of `25d5a510`, with no other change.
- **Review:** the re-check `docs/r1/reviews/CONTROLS_POSITIVE_RECHECK_REVIEW_20261126.md` (`coord-reviews-20261126` @ `28ddabf4`), ACCEPTED. The unit is tier S (R1-CONTROLS-ROW), so the notes are fixed without a further round.

## What changed

- **N3 (blocked the merge):** `r1/tests/test_controls_positive.py::test_critical_values` now asserts `places=7`. scipy 1.11.1 differs from the asserted value at about 5e-9.
- **N1:** "tier S" is kept. The report, the script's docstring and tables string, and `tables.md` now say "re-checked (ACCEPTED)". The report cites the re-check record.
- **N2:** the report says R1-CONTROLS-ROW is now on `main` (`docs/r1/PLAN.md`; l.1473 at `166db0eb`).
- **N4:** the Monte Carlo check sentence now uses the 113 non-degenerate comparisons among the 140, "about 0.07".

`controls_positive.json` is unchanged; none of its numbers moved.

## Tests

`python -m pytest -q -p no:cacheprovider r1/tests/test_controls_positive.py` → **15 passed** (scipy 1.11.1).

## Decided alone

The tolerance: 7 places, about 1e-7, well above the 5e-9 difference between scipy versions.

## Next

The coordinator runs the full suite on base and merge, then publishes the unit with the review record (R1-AUTONOMY (3)).
