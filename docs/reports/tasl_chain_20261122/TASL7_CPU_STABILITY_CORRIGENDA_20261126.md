# TASL-7 CPU stability record — corrigenda (26 November 2026)

Review `TASL7_CPU_STABILITY_REVIEW_20261126.md` (sha 0da84977…, ACCEPTED) requested m1–m7 records/corrections;
they are applied here without changing any measurement (the reviewed record `04153a57…` is unchanged):

- **m1:** record and 282-file capture bundle are placed at the stated ops paths before commit/citation.
- **m2:** two script-hash fragments in §9 are corrected: `host_capture` actual suffix `…5be4f5aef7`, `verify_setup`
  actual suffix `…f0c302caa98`; the full hashes in `SHA256SUMS` were correct.
- **m3:** `logs/preverify.txt` is not captured; the `admin_amd_extra.txt` generator is not preserved. The captured
  host files are the record's evidence.
- **m4:** the driver docstring's "4 groups ×3" is stale; the run was **six groups ×3 = 18**.
- **m5:** "microcode comes from BIOS/UEFI" is an inference; the record's caveat stands (not proven read-only).
- **m6:** the cross-host metric difference is stated as a **host-microarchitecture hypothesis**, not a proven cause.
- **m7:** validation "8.577 s" is info-only elapsed; its wall was 8.812 s.
- Scope: TASL-7 host-local reference only — `val_return 7.710938` / sealed `7.4375`, log `f3d6e3a8…` (26,561 B),
  channel `b60323b4…` (59 B); **never compare to TASL-2's 8.703125/8.703125**; any of the six 4-CPU groups is valid;
  3 repeats is a stress, not a long-run proof; re-assert kit/env/data/pins and host state before G5 use.
