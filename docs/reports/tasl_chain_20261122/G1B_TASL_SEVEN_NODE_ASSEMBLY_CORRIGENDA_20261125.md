# Seven-node assembly — corrigenda (25 November 2026)

Review `G1B_TASL_SEVEN_NODE_ASSEMBLY_REVIEW_20261125.md` (sha 009166fd…, ACCEPTED) requested m1–m3 corrections and
m4–m6 records; they are applied here (the reviewed memo `d88eeea3…` is unchanged):

- **m1:** `mlgym_houseprice` 0.6436 is CPU wall-hours (8 cores ⇒ 5.1489 core-hours), not "CPU core-h".
- **m2:** seven GPU total is **14.0333 h** exact (50,520 s); the memo's 14.0334 is the sum of rounded rows.
- **m3:** official vs provisional differ in more than `ASSEMBLY.json`: `summary.assembly_sha256` differs, official
  adds `crosscheck_gate.json` and `floor_by_node.json`; the `runs.jsonl`/`edits.json` are identical. Provisional
  hashes: `ASSEMBLY b2104243…`, `summary` not preserved as a formal record; the provisional tree is superseded.
- **m4:** the join docstring's code-diff allowlist omits `ar-cond7a.freeze.txt`; the observed job-code difference
  between paper commits `10fd3343` and `3c3f822a` includes that file and the three recorded files.
- **m5:** the join/summarise/floor commands exited rc 0 in the host shell; host stdout captures exist and are named
  in the review (`official_join.out`, `official_summary.out`, `official_floor.out`, empty `official_floor.err`).
- **m6:** the memo's central validity condition is the job-code difference check (exact three job-path files plus the
  AR-only diff; `g1b_lib.py`, `r1/noise`, `r1/harness.py` unchanged); the summary was produced with the ungated
  summariser and the gate was re-checked by floor-by-node, with no data effect.
- Before G5 use: cite this review/memo/floor in the G5 note; report per-node D21 via the summaries (no D21
  selection); use the official tree only; TASL-7 audit chunks still need the short cross-check for the five nodes
  not covered by xc2 plus the TASL-7 isolation host check; keep AR separate; run the chain tests and record a code
  review before reusing `g1b_tasl_join.py` for further assemblies.
