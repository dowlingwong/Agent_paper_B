# G.4b re-pilot result — corrigenda (25 November 2026)

Review `G4B_TASL_PILOT_RESULT_REVIEW_20261125.md` (sha a04b490e…, ACCEPTED) requested m1–m4 corrections and records
m5–m7; they are applied here without changing any measured value (the reviewed memo `af74c536…` is unchanged):

- **m1:** the "+5 days" sentence in §8 applies to the seven-node comparison only; the eight-node binding moves all
  four values by +11 days (2026-12-11/12-14, 2027-01-09, 2027-01-16).
- **m2:** `step6_dates.log` lives on TASL-2, not TASL-7; the report's TASL-7 inventory is corrected here.
- **m3:** the `step6_dates.log` "key values" block prints target dates labelled as computed dates; the two JSONs
  (`dates_g5` e3f6f485…, `dates_g4` 75f531ca…) are correct and are the record.
- **m4:** `step2_smoke.log`'s harness-check JSON is truncated at its start and `step3_reclass.log`'s summary prints
  `None`/empty nested keys; the sealed smoke/reclass JSONs and captures are the complete evidence.
- **m5:** the "~33 s clock-skew" note has no simultaneous capture; cross-host ordering still holds by ~10 min.
- **m6:** `harness_g5` exists only on TASL-2, not TASL-7; "untouched on both hosts" is corrected to the checkouts
  actually present.
- **m7:** the new re-classification JSON inside the G.4 records directory is a same-directory addition, disclosed in
  §3/§10; no G.4 record was modified.

Dates remain **changed but not applied** (R1-BX-D14 (iii)); before application the author must choose the eight-node
G.5 binding vs the G.4-like seven-node basis, re-anchor `--today`, and note that G.5's `pilot_basis`/P3 still read the
G.4 spec.
