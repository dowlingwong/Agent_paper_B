# Build P3 — executor response to review round 2 (16 Nov 2026)

ENGINEERING_ONLY. Review: `BUILD_P3_REVIEW_20261116.md`, Round 2 — **ACCEPT** (5 MINOR). All five handled after acceptance. The table was rebuilt in full because the fingerprint now covers `table.py`; apart from the fingerprint and timing fields it is identical to the table the reviewer reproduced at `8d37ff8` (checked by script), so no certified number changed.

| # | Finding | Change |
|---|---|---|
| R2-1 | false explanation of the novelty member | corrected in the report (§5.2), `families.py` and response R1: the round-1 novelty member still gains about +0.0010 over the same best static; the schedule replaced it because its gain is about six times larger |
| R2-2 | coarse static grid | stated as a caveat in the report (§1) and `families.py`, with the reviewer's measurement (information: a finer grid beats the selected static by 0.00022 ± 0.00008); a refinement pass is recorded in BUILD_STATUS as an open item before P4 uses the oracle references |
| R2-3 | null's evaluated member vacuous; "strong falsification test" | the claim is withdrawn in `families.py` and the report: in the null the exact DP dominates every schedule; the null result rests on the exact DP and the Dynamic family's evaluation |
| R2-4 | fingerprint misses the producer | `table.py` added to `SOURCES`; every world record stores its own `code_sha256`; `test_table_is_current` checks both; full rebuild |
| R2-5 | schedule wording | "after Track S's (not a port)", with the budget position runs used / W and the fixed τ split stated in `policies.py`, `families.py` and the report; §5.2 says the gain comes almost entirely from the budget-third dependence (+0.0060 without the τ split, +0.0001 with the τ split alone) |
