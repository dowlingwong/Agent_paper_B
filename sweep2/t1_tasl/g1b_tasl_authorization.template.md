# Authorizations for T1 on the TASL pair (ENGINEERING_ONLY) — TEMPLATES

Copy each block to its file under `docs/r1/authorizations/`, fill every field, have the author sign, and publish it
byte-identically on `main`. `g1b_tasl.py run-node` and `g4_tasl.py run-node` / `serve` refuse without it. Prepared by
the Mac-desk agent (Claude), AI-assisted.

## G.1b: `docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md`

```
approved: false
label: ENGINEERING_ONLY
labels_read: none
paper_commit: <spec.paper.commit: a main commit whose code equals the launch checkout's (verify_launch_tasl)>
spec_sha256: <sha256 of sweep2/t1_tasl/g1b_tasl_spec.json at the launch commit>
run_id: <spec.run_id>
harness_commit: <spec.harness.commit, the bare 40-character sha>
host_row: R1-T1-TASL-ENV
P1: PASS — R1-T1-HOST-TASL: G.1b on TASL-2 and TASL-7, one GPU model (RTX 4090)
P2: PASS — TASL-2 harness-isolation host check <hosts.TASL-2.isolation_host_check.record>
P3: PASS — TASL-7 harness-isolation host check <hosts.TASL-7.isolation_host_check.record>
P4: PASS — independent review docs/r1/reviews/<the T1 TASL review>.md
P5: PASS — R1-G1B-EDITS: <n> declared edits, <runs> runs per node
P6: PASS — R1-G1B-TIMEOUT: <census_baseline_x3 | census_slowest_x3>
```

## G.4: `docs/r1/authorizations/g4_t1_tasl_<YYYYMMDD>.md`

```
approved: false
label: ENGINEERING_ONLY
labels_read: none
paper_commit: <spec.paper.commit: a main commit whose code equals the launch checkout's (verify_launch_tasl)>
spec_sha256: <sha256 of sweep2/t1_tasl/g4_tasl_spec.json at the launch commit>
run_id: <spec.run_id>
harness_commit: <spec.harness.commit, the bare 40-character sha>
P1: PASS — R1-T1-HOST-TASL: worker TASL-2, proposer TASL-7; TASL-2 host check <worker.isolation_host_check.record>
P2: PASS — R1-TRACKG-G3-EARLY: pilot nodes mlab_cifar10, mlgym_fmnist, <autoresearch_fixedtokens | mlgym_breakout_minatar>
P3: PASS — G.1b and the TASL-7 lease: <docs/r1/authorizations/g1b_t1_tasl_<date>.md ...> (the order of decision G4-ORDER)
P4: PASS — independent review docs/r1/reviews/<the T1 TASL review>.md
P5: PASS — R1-T1-TASL-ENV: proposer binary, bin-directory manifest and GGUF as in the spec
```
