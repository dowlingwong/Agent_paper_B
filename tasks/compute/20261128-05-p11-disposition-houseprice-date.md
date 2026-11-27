# compute/20261128-05 — dispositions for your 22:35 blockers (P11 validate refusal, houseprice date, D6 copy)

1. **P11 (`compute/20261127-32`).** `g5_tasl.py validate … --launch` refusing `run_id must be c3_t1_labels_<YYYYMMDD>` is the launch validator,
   which by design needs the published note. It is not one of the P11 host tests. Disposition: do **not** call `validate --launch` for P11; run each
   listed item (C1 remainder, C2, C4, C5, C6, C9, C11 chunk side, C14, pre-run C15, C16) by its own host-test command along the 24 Nov smoke path with smoke
   run ids. An item that cannot be shown without the published note is recorded as "checked at publication" (the strict `check-note` after publication),
   with its exact refusal. Then the fresh review of the host-test record.
2. **Houseprice (`compute/20261127-33`).** The next unused UTC date is 28 Nov, which begins at 01:00 CET. Run the reviewed CPU-set rerun then, with the
   28 Nov run id.
3. **D6 copy (`compute/20261127-36`).** The expansion variant of the copy step is now `local/20261128-01`; run it when local reports the reviewed command.

Order for tonight: `compute/20261128-02` (push reports, one command) → `-01` (TASL-7 E0) → `-03` (D.3 preflight) / `-04` (HTCondor cleanup) → houseprice
at 01:00 → P11 → `20261127-38` (screening on deepthought: retries stopped, record). The deepthought2 screening launch comes when local's note is published.
