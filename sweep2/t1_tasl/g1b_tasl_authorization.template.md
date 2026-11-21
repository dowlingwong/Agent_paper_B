# Authorization: G.1b T1 noise floors on the TASL pair (ENGINEERING_ONLY) — TEMPLATE

Copy to `docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md`, fill every field, have the author sign, and publish it
byte-identically on `main`. `g1b_tasl.py run-node` refuses without it. Prepared by the Mac-desk agent (Claude),
AI-assisted.

```
approved: false
label: ENGINEERING_ONLY
labels_read: none
paper_commit: <the launch commit, descending from published main>
spec_sha256: <sha256 of sweep2/t1_tasl/g1b_tasl_spec.json at the launch commit>
host_row: R1-T1-TASL-ENV
P1: PASS — R1-T1-HOST-TASL: worker on TASL-2 (and TASL-7 for G.1b), one GPU model (RTX 4090)
P2: PASS — TASL-2 harness-isolation host checks: <report path, sha256>
P3: PASS — TASL-7 harness-isolation host checks: <report path, sha256>
P4: PASS — independent review docs/r1/reviews/<the T1 TASL review>.md
P5: PASS — R1-G1B-EDITS: <n> declared edits, <runs> runs per node
P6: PASS — R1-G1B-TIMEOUT: <census_baseline_x3 | census_slowest_x3>
```
